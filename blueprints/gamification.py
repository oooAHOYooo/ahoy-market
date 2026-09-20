"""
Gamification Blueprint - XP, Badges, and Leaderboards
"""
from flask import Blueprint, jsonify, current_app
from flask_login import current_user
from db import get_session
from models import Tip, User
from decimal import Decimal

bp = Blueprint('gamification', __name__, url_prefix='/api/gamification')


def calculate_badges(total_boosted):
    """Return list of badges earned based on total USD boosted."""
    badges = []
    if total_boosted >= Decimal('10'):
        badges.append('Supporter')
    if total_boosted >= Decimal('50'):
        badges.append('Champion')
    if total_boosted >= Decimal('200'):
        badges.append('Patron')
    if total_boosted >= Decimal('500'):
        badges.append('Legend')
    return badges


@bp.route('/user/boost-stats', methods=['GET'])
def get_user_boost_stats():
    """
    Get current user's boost statistics (XP, badges, total boosted, boost count).
    Requires authentication.

    Returns:
    {
      "xp": 42.50,
      "badges": ["Supporter", "Champion"],
      "total_boosted": 42.50,
      "boost_count": 5,
      "next_badge": "Patron",
      "next_badge_amount": 200.00,
      "progress_to_next": 21.25  # percentage
    }
    """
    if not current_user.is_authenticated:
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        with get_session() as db_session:
            from sqlalchemy import func

            # Sum all tips from current user using SQL aggregation
            result = db_session.query(
                func.sum(Tip.amount).label('total_amount'),
                func.count(Tip.id).label('count')
            ).filter(Tip.user_id == current_user.id).first()

            total_amount = result.total_amount or 0
            boost_count = result.count or 0
            total_boosted = Decimal(str(total_amount))
            xp = float(total_boosted)  # XP = $1 boosted = 1 XP

            badges = calculate_badges(total_boosted)

            # Determine next badge
            next_badge = None
            next_badge_amount = None
            progress_to_next = None

            badge_thresholds = [
                ('Supporter', Decimal('10')),
                ('Champion', Decimal('50')),
                ('Patron', Decimal('200')),
                ('Legend', Decimal('500'))
            ]

            for badge_name, threshold in badge_thresholds:
                if total_boosted < threshold:
                    next_badge = badge_name
                    next_badge_amount = float(threshold)
                    if threshold > 0:
                        progress_to_next = min(100, float((total_boosted / threshold) * 100))
                    break

            return jsonify({
                'xp': xp,
                'badges': badges,
                'total_boosted': float(total_boosted),
                'boost_count': boost_count,
                'next_badge': next_badge,
                'next_badge_amount': next_badge_amount,
                'progress_to_next': progress_to_next
            }), 200
    except Exception as e:
        current_app.logger.error(f'Error getting boost stats: {e}', exc_info=True)
        return jsonify({'error': 'Failed to fetch boost stats'}), 500


@bp.route('/leaderboard/boosters', methods=['GET'])
def get_boosters_leaderboard():
    """
    Get top boosters leaderboard (top 20 all-time).
    Public endpoint (no auth required).

    Returns:
    {
      "leaderboard": []
    }
    """
    return jsonify({'leaderboard': []}), 200
