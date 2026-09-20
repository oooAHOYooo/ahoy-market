from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass
class BackfillResult:
    inserted: int = 0
    skipped: int = 0
    errors: int = 0


def _existing_event(session, event_type: str, source_table: str, source_id: str):
    from models import AnalyticsEvent

    return session.query(AnalyticsEvent.id).filter(
        AnalyticsEvent.event_type == event_type,
        AnalyticsEvent.metadata_json["source_table"].as_string() == source_table,
        AnalyticsEvent.metadata_json["source_id"].as_string() == str(source_id),
    ).first()


def _add_event(session, *, event_type: str, path: str | None, user_id: int | None, ip_address: str | None, session_id: str | None, created_at: datetime, metadata: dict):
    from models import AnalyticsEvent

    event = AnalyticsEvent(
        event_type=event_type,
        path=path,
        user_id=user_id,
        ip_address=ip_address,
        session_id=session_id,
        created_at=created_at,
        metadata_json=metadata,
    )
    session.add(event)


def backfill_analytics(session_factory, source_tables: list[str] | None = None, dry_run: bool = False) -> BackfillResult:
    """Backfill recoverable historical analytics into analytics_events.

    This is intentionally conservative: it only emits events we can infer from
    existing first-party tables and it tags every inserted row so the process is
    idempotent.
    """
    from models import User, Purchase, Tip, WalletTransaction

    source_tables = source_tables or ["users", "purchases", "tips", "wallet_transactions"]
    result = BackfillResult()

    with session_factory() as session:
        if "users" in source_tables:
            for user in session.query(User).order_by(User.created_at.asc()).all():
                try:
                    if _existing_event(session, "user_signed_up", "users", user.id):
                        result.skipped += 1
                        continue
                    _add_event(
                        session,
                        event_type="user_signed_up",
                        path="/auth/register",
                        user_id=user.id,
                        ip_address=None,
                        session_id=f"backfill:user:{user.id}",
                        created_at=user.created_at,
                        metadata={
                            "source_table": "users",
                            "source_id": str(user.id),
                            "signup_method": "historical_backfill",
                            "username": user.username,
                            "email": user.email,
                        },
                    )
                    result.inserted += 1
                except Exception:
                    result.errors += 1

        if "purchases" in source_tables:
            for purchase in session.query(Purchase).order_by(Purchase.created_at.asc()).all():
                try:
                    if _existing_event(session, "purchase_recorded", "purchases", purchase.id):
                        result.skipped += 1
                        continue
                    _add_event(
                        session,
                        event_type="purchase_recorded",
                        path="/merch",
                        user_id=purchase.user_id,
                        ip_address=None,
                        session_id=f"backfill:purchase:{purchase.id}",
                        created_at=purchase.created_at,
                        metadata={
                            "source_table": "purchases",
                            "source_id": str(purchase.id),
                            "purchase_type": purchase.type,
                            "status": purchase.status,
                            "total": float(purchase.total or 0),
                            "item_id": purchase.item_id,
                        },
                    )
                    result.inserted += 1
                except Exception:
                    result.errors += 1

        if "tips" in source_tables:
            for tip in session.query(Tip).order_by(Tip.created_at.asc()).all():
                try:
                    if _existing_event(session, "tip_recorded", "tips", tip.id):
                        result.skipped += 1
                        continue
                    _add_event(
                        session,
                        event_type="tip_recorded",
                        path="/support",
                        user_id=tip.user_id,
                        ip_address=None,
                        session_id=f"backfill:tip:{tip.id}",
                        created_at=tip.created_at,
                        metadata={
                            "source_table": "tips",
                            "source_id": str(tip.id),
                            "artist_id": tip.artist_id,
                            "amount": float(tip.amount or 0),
                            "artist_payout": float(tip.artist_payout or 0),
                        },
                    )
                    result.inserted += 1
                except Exception:
                    result.errors += 1

        if "wallet_transactions" in source_tables:
            for tx in session.query(WalletTransaction).order_by(WalletTransaction.created_at.asc()).all():
                try:
                    if _existing_event(session, "wallet_funded", "wallet_transactions", tx.id):
                        result.skipped += 1
                        continue
                    _add_event(
                        session,
                        event_type="wallet_funded",
                        path="/wallet",
                        user_id=tx.user_id,
                        ip_address=None,
                        session_id=f"backfill:wallet:{tx.id}",
                        created_at=tx.created_at,
                        metadata={
                            "source_table": "wallet_transactions",
                            "source_id": str(tx.id),
                            "amount": float(tx.amount or 0),
                            "balance_after": float(tx.balance_after or 0),
                            "type": tx.type,
                        },
                    )
                    result.inserted += 1
                except Exception:
                    result.errors += 1

        if not dry_run:
            session.commit()
        else:
            session.rollback()

    return result
