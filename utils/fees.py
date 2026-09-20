"""
Centralized fee calculation for payments and boosts.

All payment-related fee constants and calculations should be here
to ensure consistency across the platform.
"""
from decimal import Decimal


# Fee Constants - single source of truth
PLATFORM_FEE_PERCENT = Decimal("0.075")  # 7.5% (boosts)
STRIPE_PERCENTAGE = Decimal("0.029")     # 2.9%
STRIPE_FIXED = Decimal("0.30")           # $0.30

# Tab subscription flat fee
AHOY_TAB_FEE = Decimal("4.00")          # $4 flat to Ahoy per billing cycle

# Tab tiers: (payment_amount, wallet_amount, label)
TAB_TIERS = [
    (Decimal("14.00"), Decimal("10.00"), "Starter"),
    (Decimal("24.00"), Decimal("20.00"), "Regular"),
    (Decimal("54.00"), Decimal("50.00"), "Heavy"),
]


def calculate_boost_fees(boost_amount: Decimal):
    """
    Calculate all fees for a boost.

    Logic:
    - Artist receives 100% of boost_amount
    - Tipper pays: boost_amount + stripe_fee + platform_fee

    Args:
        boost_amount: The amount the tipper wants to give to the artist

    Returns:
        tuple: (stripe_fee, platform_fee, total_charge, artist_payout, platform_revenue)
    """
    # Round boost amount to 2 decimals
    boost_amount = round(boost_amount, 2)

    # Calculate Stripe fee: (boost_amount * 2.9%) + $0.30
    stripe_fee = round((boost_amount * STRIPE_PERCENTAGE) + STRIPE_FIXED, 2)

    # Calculate platform fee: boost_amount * 7.5%
    platform_fee = round(boost_amount * PLATFORM_FEE_PERCENT, 2)

    # Total charge to tipper
    total_charge = round(boost_amount + stripe_fee + platform_fee, 2)

    # Artist receives 100% of boost amount
    artist_payout = boost_amount

    # Platform revenue is the platform fee
    platform_revenue = platform_fee

    return stripe_fee, platform_fee, total_charge, artist_payout, platform_revenue


def calculate_tab_fees(payment_amount: Decimal):
    """
    Calculate Tab subscription fees.

    User pays payment_amount/mo. $4 flat goes to Ahoy. Rest is artist wallet.
    Stripe fee on top of payment_amount.

    Args:
        payment_amount: What the user pays (e.g. $14, $24, $54, or custom)

    Returns:
        tuple: (ahoy_fee, stripe_fee, total_charge, wallet_amount)

    Examples:
        $14/mo: $4 Ahoy + $0.71 Stripe = $14.71 total, $10 wallet
        $24/mo: $4 Ahoy + $1.00 Stripe = $25.00 total, $20 wallet
        $54/mo: $4 Ahoy + $1.87 Stripe = $55.87 total, $50 wallet
    """
    payment_amount = round(Decimal(str(payment_amount)), 2)
    if payment_amount < Decimal("14.00"):
        raise ValueError("Minimum Tab payment is $14.00")

    wallet_amount = payment_amount - AHOY_TAB_FEE
    stripe_fee = round((payment_amount * STRIPE_PERCENTAGE) + STRIPE_FIXED, 2)
    total_charge = payment_amount + stripe_fee

    return AHOY_TAB_FEE, stripe_fee, total_charge, wallet_amount


def calculate_fee_and_net(amount: Decimal):
    """
    Calculate platform fee and net amount after fee.

    Used for simple fee calculations where we just need to know
    the platform's cut and what remains.

    Args:
        amount: The total amount

    Returns:
        tuple: (fee, net) where fee is platform's cut and net is remainder
    """
    fee = amount * PLATFORM_FEE_PERCENT
    net = amount - fee
    return fee, net
