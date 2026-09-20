import os
from decimal import Decimal
from flask import Blueprint, jsonify, request, current_app
import stripe
try:
    from stripe._error import StripeError as _StripeError
except ImportError:
    _StripeError = getattr(getattr(stripe, "error", None), "StripeError", Exception)  # type: ignore
from db import get_session
from models import Tip
from datetime import datetime
from services.user_resolver import resolve_db_user_id
from utils.fees import calculate_boost_fees
from utils.posthog_client import get_posthog_client

bp = Blueprint("boost_stripe", __name__, url_prefix="/api/boost/stripe")
# Back-compat/alias blueprint to expose /api/boost/confirm as requested
boost_api_bp = Blueprint("boost_api", __name__, url_prefix="/api/boost")


def _configure_stripe_from_config():
    # Prefer Flask config if set, else environment variables
    cfg = getattr(current_app, "config", {})
    api_key = cfg.get("STRIPE_SECRET_KEY") or os.getenv("STRIPE_SECRET_KEY") or os.getenv("STRIPE_SECRET_KEY_TEST")
    stripe.api_key = api_key


@bp.route("/create-intent", methods=["POST"])
def create_payment_intent():
    """
    Create a Stripe PaymentIntent for an artist boost OR a multi-item cart.

    Single boost body:
      { "artist_id": string, "boost_amount": number, "ahoy_match": number }

    Cart body:
      { "items": [{ "artist_id": string, "artist_name": string, "amount": number }], "source": string }
    """
    _configure_stripe_from_config()
    if not stripe.api_key:
        return jsonify({"error": "Stripe not configured"}), 500

    data = request.get_json(silent=True) or {}
    source = (data.get("source") or "web").strip()[:32]

    # ---- Detect cart vs single boost ----
    cart_items = data.get("items")
    is_cart = isinstance(cart_items, list) and len(cart_items) > 0

    if is_cart:
        # Validate and sum cart
        total_boost = Decimal("0.00")
        validated_items = []
        for idx, item in enumerate(cart_items):
            aid = str(item.get("artist_id") or "").strip()
            aname = str(item.get("artist_name") or aid).strip()
            try:
                amt = Decimal(str(item.get("amount") or "0"))
            except Exception:
                return jsonify({"error": f"Invalid amount for item {idx}"}), 400
            if amt < Decimal("0.50"):
                return jsonify({"error": f"Minimum boost is $0.50 per artist (got ${amt} for {aid})"}), 400
            if not aid:
                return jsonify({"error": f"artist_id required for item {idx}"}), 400
            validated_items.append({"artist_id": aid, "artist_name": aname, "amount": amt})
            total_boost += amt

        artist_id = "cart"
        artist_name = f"{len(validated_items)} Artists"
        boost_amount_decimal = total_boost
        ahoy_match = Decimal("0.00")
        match_decimal = Decimal("0.00")
        # Serialize cart for metadata (Stripe has 500 char limit per value)
        import json as _json
        cart_json = _json.dumps([{"id": i["artist_id"], "name": i["artist_name"], "amt": str(i["amount"])} for i in validated_items])
        if len(cart_json) > 490:
            # Truncate names to fit
            cart_json = _json.dumps([{"id": i["artist_id"], "amt": str(i["amount"])} for i in validated_items])
    else:
        # Single boost (existing behaviour)
        artist_id = data.get("artist_id")
        artist_name = (data.get("artist_name") or "").strip() or str(artist_id or "").replace("-", " ").title()
        boost_amount = data.get("boost_amount") or data.get("amount")
        ahoy_match = data.get("ahoy_match") or 0.0

        if not artist_id or (isinstance(artist_id, str) and not artist_id.strip()):
            return jsonify({"error": "artist_id is required and cannot be empty"}), 400
        if boost_amount is None:
            return jsonify({"error": "boost_amount is required"}), 400

        try:
            boost_amount_decimal = Decimal(str(boost_amount))
        except (ValueError, TypeError):
            return jsonify({"error": f"Invalid boost amount: {boost_amount}"}), 400

        if boost_amount_decimal < Decimal("0.50"):
            return jsonify({"error": f"Minimum boost amount is $0.50, got ${boost_amount_decimal}"}), 400

        cart_json = ""

        try:
            match_decimal = Decimal(str(ahoy_match))
        except (ValueError, TypeError):
            match_decimal = Decimal("0.00")

    # Resolve user if logged in (optional)
    user_id = resolve_db_user_id()

    # Calculate fee breakdown
    stripe_fee, platform_fee, total_charge, artist_payout, platform_revenue = calculate_boost_fees(boost_amount_decimal)

    if not is_cart:
        # Add Ahoy match to total for single boosts
        try:
            match_decimal = Decimal(str(ahoy_match))
            total_charge += match_decimal
            platform_revenue += match_decimal
        except (ValueError, TypeError):
            match_decimal = Decimal("0.00")
    else:
        match_decimal = Decimal("0.00")

    # Look up user email
    user_email = ""
    if user_id:
        try:
            from models import User
            with get_session() as s:
                u = s.query(User).filter(User.id == user_id).first()
                user_email = (u.email or "") if u else ""
        except Exception:
            user_email = ""

    now = datetime.utcnow()
    payout_period = now.strftime("%Y-%m")
    artist_slug_short = str(artist_id)[:12].upper().replace(" ", "-")
    boost_sku = f"BST-{now.strftime('%y%m')}-{artist_slug_short}-{int(now.timestamp()) % 100000:05d}"

    suffix_raw = f"BOOST {artist_name}"[:22]
    statement_suffix = "".join(c for c in suffix_raw if c.isalnum() or c == " ").strip() or "BOOST"

    try:
        metadata = {
            "artist_id": str(artist_id),
            "artist_name": artist_name,
            "user_id": str(user_id or ""),
            "user_email": user_email,
            "source": source,
            "boost_type": "cart" if is_cart else "boost",
            "boost_sku": boost_sku,
            "payout_period": payout_period,
            "boost_amount": str(boost_amount_decimal),
            "stripe_fee": str(stripe_fee),
            "platform_fee": str(platform_fee),
            "total_paid": str(total_charge),
            "artist_payout": str(artist_payout),
            "platform_revenue": str(platform_revenue),
            "ahoy_match": str(match_decimal),
        }
        if is_cart and cart_json:
            metadata["cart_items"] = cart_json

        intent_kwargs = {
            "amount": int(total_charge * 100),
            "currency": "usd",
            "automatic_payment_methods": {"enabled": True},
            "description": f"Boost: {artist_name}",
            "statement_descriptor_suffix": statement_suffix,
            "metadata": metadata,
        }
        if user_email:
            intent_kwargs["receipt_email"] = user_email
        intent = stripe.PaymentIntent.create(**intent_kwargs)

        try:
            ph = get_posthog_client()
            if ph:
                ph.capture(
                    distinct_id=str(user_id) if user_id else "anonymous",
                    event="boost_payment_initiated",
                    properties={
                        "artist_id": str(artist_id),
                        "boost_amount": float(boost_amount_decimal),
                        "total_charge": float(total_charge),
                        "ahoy_match": float(match_decimal),
                        "source": source,
                        "is_cart": is_cart,
                        "cart_item_count": len(validated_items) if is_cart else 1,
                    },
                )
        except Exception:
            pass

        return jsonify({"client_secret": intent.client_secret}), 200
    except _StripeError as e:
        current_app.logger.exception("create_payment_intent: Stripe error")
        return jsonify({"error": str(e) or "Stripe error creating payment intent"}), 400
    except Exception as e:
        current_app.logger.exception("create_payment_intent: unexpected error")
        return jsonify({"error": str(e) or "Unexpected error creating payment intent"}), 500



@bp.route("/confirm", methods=["POST"])
def confirm_boost_record():
    """
    Optional: Client can call after successful payment to ensure ledger is updated.
    Body: { "payment_intent_id": string }
    This endpoint is idempotent; if a record already exists, it returns success.
    """
    _configure_stripe_from_config()
    if not stripe.api_key:
        return jsonify({"error": "Stripe not configured"}), 500

    data = request.get_json(silent=True) or {}
    payment_intent_id = data.get("payment_intent_id")
    if not payment_intent_id:
        return jsonify({"error": "payment_intent_id required"}), 400

    try:
        intent = stripe.PaymentIntent.retrieve(payment_intent_id)
        if intent.status != "succeeded":
            return jsonify({"error": "Payment not succeeded"}), 400

        # Stripe SDK 13+: StripeObject has no .get(); convert to plain dict first.
        try:
            metadata = dict(intent.to_dict().get("metadata") or {})
        except Exception:
            metadata = {}
        artist_id = metadata.get("artist_id")
        boost_amount_str = metadata.get("boost_amount")
        stripe_fee_str = metadata.get("stripe_fee")
        platform_fee_str = metadata.get("platform_fee")
        total_paid_str = metadata.get("total_paid")
        artist_payout_str = metadata.get("artist_payout")
        platform_revenue_str = metadata.get("platform_revenue") or platform_fee_str
        ahoy_match_str = metadata.get("ahoy_match") or "0.00"
        user_id_str = metadata.get("user_id") or ""
        user_id = int(user_id_str) if user_id_str.isdigit() else None

        if not all([artist_id, boost_amount_str, platform_fee_str, total_paid_str]):
            return jsonify({"error": "Missing metadata to record boost"}), 400

        # Cast to string for Decimal to avoid lint errors with Optional[Any]
        artist_id = str(artist_id)
        boost_amount_str = str(boost_amount_str)
        stripe_fee_str = str(stripe_fee_str or "0.00")
        platform_fee_str = str(platform_fee_str)
        total_paid_str = str(total_paid_str)
        artist_payout_str = str(artist_payout_str or boost_amount_str)
        platform_revenue_str = str(platform_revenue_str or platform_fee_str)
        ahoy_match_str = str(ahoy_match_str)

        boost_type = metadata.get("boost_type") or "boost"
        is_cart_confirm = boost_type == "cart"

        with get_session() as db_session:
            # Idempotency: if we already recorded this PI, return success
            existing = db_session.query(Tip).filter(Tip.stripe_payment_intent_id == payment_intent_id).first()
            if existing:
                return jsonify({"status": "ok", "recorded": True}), 200

            tip_datetime = datetime.utcnow()

            if is_cart_confirm:
                # --- Cart: write one Tip per artist ---
                import json as _json
                cart_json_str = metadata.get("cart_items") or "[]"
                try:
                    cart_list = _json.loads(cart_json_str)
                except Exception:
                    cart_list = []

                total_boost_decimal = Decimal(boost_amount_str)
                stripe_fee_decimal = Decimal(stripe_fee_str)
                platform_fee_decimal = Decimal(platform_fee_str)

                for cart_item in cart_list:
                    item_aid = str(cart_item.get("id") or cart_item.get("artist_id") or "unknown")
                    item_amt = Decimal(str(cart_item.get("amt") or cart_item.get("amount") or "0"))
                    # Proportional fee split
                    weight = item_amt / total_boost_decimal if total_boost_decimal else Decimal("0")
                    item_stripe_fee = (stripe_fee_decimal * weight).quantize(Decimal("0.01"))
                    item_platform_fee = (platform_fee_decimal * weight).quantize(Decimal("0.01"))
                    item_total_paid = item_amt + item_stripe_fee + item_platform_fee
                    item_payout = item_amt - item_platform_fee

                    tip = Tip(
                        user_id=user_id,
                        artist_id=item_aid,
                        amount=item_amt,
                        fee=item_platform_fee,
                        platform_fee=item_platform_fee,
                        net_amount=item_payout,
                        stripe_fee=item_stripe_fee,
                        total_paid=item_total_paid,
                        artist_payout=item_payout,
                        platform_revenue=item_platform_fee,
                        ahoy_match=Decimal("0.00"),
                        stripe_payment_intent_id=payment_intent_id,
                        created_at=tip_datetime,
                    )
                    db_session.add(tip)
                    if user_id:
                        from blueprints.payments import update_user_artist_position
                        update_user_artist_position(
                            user_id=user_id,
                            artist_id=item_aid,
                            boost_amount=item_amt,
                            boost_datetime=tip_datetime,
                            db_session=db_session,
                        )
            else:
                # --- Single boost ---
                tip = Tip(
                    user_id=user_id,
                    artist_id=str(artist_id),
                    amount=Decimal(boost_amount_str),
                    fee=Decimal(platform_fee_str),
                    platform_fee=Decimal(platform_fee_str),
                    net_amount=Decimal(artist_payout_str) if artist_payout_str else Decimal(boost_amount_str),
                    stripe_fee=Decimal(stripe_fee_str) if stripe_fee_str else Decimal("0.00"),
                    total_paid=Decimal(total_paid_str),
                    artist_payout=Decimal(artist_payout_str) if artist_payout_str else Decimal(boost_amount_str),
                    platform_revenue=Decimal(platform_revenue_str) if platform_revenue_str else Decimal(platform_fee_str),
                    ahoy_match=Decimal(ahoy_match_str),
                    stripe_payment_intent_id=payment_intent_id,
                    created_at=tip_datetime,
                )
                db_session.add(tip)
                if user_id:
                    from blueprints.payments import update_user_artist_position
                    update_user_artist_position(
                        user_id=user_id,
                        artist_id=str(artist_id),
                        boost_amount=Decimal(boost_amount_str),
                        boost_datetime=tip_datetime,
                        db_session=db_session,
                    )

            db_session.commit()

        # PostHog: boost payment confirmed by client
        try:
            ph = get_posthog_client()
            if ph:
                ph.capture(
                    distinct_id=str(user_id) if user_id else "anonymous",
                    event="boost_payment_confirmed",
                    properties={
                        "artist_id": artist_id,
                        "boost_amount": float(Decimal(boost_amount_str)),
                        "total_paid": float(Decimal(total_paid_str)),
                        "payment_intent_id": payment_intent_id,
                        "is_cart": is_cart_confirm,
                    },
                )
        except Exception:
            pass

        return jsonify({"status": "ok", "recorded": True}), 200
    except _StripeError as e:
        current_app.logger.exception("confirm_boost_record: Stripe error")
        return jsonify({"error": str(e) or "Stripe error confirming boost"}), 400
    except Exception as e:
        current_app.logger.exception("confirm_boost_record: unexpected error")
        return jsonify({"error": str(e) or "Unexpected error confirming boost"}), 500

# Alias route: /api/boost/confirm
@boost_api_bp.route("/confirm", methods=["POST"])
def confirm_boost_record_alias():
    return confirm_boost_record()

