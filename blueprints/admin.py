from flask import Blueprint, jsonify, request, current_app, make_response, session as flask_session
from flask_login import login_required, current_user
from sqlalchemy import text
from db import get_session
from datetime import datetime
from functools import wraps
import uuid
from models import (
    User, Tip, Purchase, Feedback, ArtistClaim, ArtistTip, AnalyticsEvent, AuditLog,
    Track, Show, ContentArtist, Event, ContentMerch, ContentVideo, WhatsNewItem,
    PodcastShow, PodcastEpisode, StudioCollection
)

bp = Blueprint('admin', __name__, url_prefix='/api/admin')

def admin_only(f):
    """Decorator: require admin authentication."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            return jsonify({'error': 'Admin access required'}), 403
        return f(*args, **kwargs)
    return decorated_function

def log_audit(action, target_type, target_id, details=None):
    """Log an admin action for audit trail."""
    with get_session() as session:
        audit = AuditLog(
            admin_id=current_user.id if current_user.is_authenticated else None,
            action=action,
            target_type=target_type,
            target_id=target_id,
            details=details
        )
        session.add(audit)
        session.commit()

_ALWAYS_EXCLUDED_IPS = {'127.0.0.1', '::1'}

def _get_client_ip():
    """Return client IP, or None if it should be excluded from analytics."""
    ip = request.remote_addr
    if not ip:
        return None
    excluded = current_app.config.get('ANALYTICS_EXCLUDED_IPS') or set()
    if ip in _ALWAYS_EXCLUDED_IPS or ip in excluded:
        return None
    return ip


def _get_visitor_id():
    """Return a stable anonymous visitor id, creating one if needed."""
    visitor_id = request.cookies.get("ahoy_visitor_id")
    if visitor_id:
        return visitor_id, False
    return uuid.uuid4().hex, True

@bp.route('/stats', methods=['GET'])
@admin_only
def get_stats():
    with get_session() as session:
        user_count = session.query(User).count()
        tip_count = session.query(Tip).count()
        purchase_count = session.query(Purchase).count()
        revenue = session.execute(text("SELECT SUM(total) FROM purchases WHERE status = 'paid'")).scalar() or 0
        tip_total = session.execute(text("SELECT SUM(amount) FROM tips")).scalar() or 0
        
    return jsonify({
        'users': user_count,
        'tips': tip_count,
        'purchases': purchase_count,
        'revenue': float(revenue),
        'tip_total': float(tip_total)
    })

@bp.route('/activity', methods=['GET'])
@admin_only
def get_activity():
    with get_session() as session:
        # Recent Users
        users = session.query(User).order_by(User.created_at.desc()).limit(10).all()
        user_events = [{
            'type': 'signup',
            'text': f"New user signed up: {u.username or u.email}",
            'date': u.created_at,
            'user_id': u.id
        } for u in users]

        # Recent Tips
        tips = session.query(Tip).order_by(Tip.created_at.desc()).limit(10).all()
        tip_events = [{
            'type': 'tip',
            'text': f"Tip of ${t.amount} to {t.artist_id}",
            'date': t.created_at,
            'user_id': t.user_id
        } for t in tips]
        
        # Recent Purchases
        purchases = session.query(Purchase).order_by(Purchase.created_at.desc()).limit(10).all()
        purchase_events = [{
            'type': 'purchase',
            'text': f"Purchase of {p.item_id} for ${p.total}",
            'date': p.created_at,
            'user_id': p.user_id
        } for p in purchases]
        
        # Recent Feedback
        feedbacks = session.query(Feedback).order_by(Feedback.created_at.desc()).limit(10).all()
        feedback_events = [{
            'type': 'feedback',
            'text': f"Feedback: {f.message[:50]}...",
            'date': f.created_at,
            'user_id': f.user_id,
            'id': f.id
        } for f in feedbacks]
        
        # Claims
        claims = session.query(ArtistClaim).order_by(ArtistClaim.created_at.desc()).limit(10).all()
        claim_events = [{
            'type': 'claim',
            'text': f"Artist Claim: {c.artist_id} by User {c.user_id}",
            'date': c.created_at,
            'user_id': c.user_id
        } for c in claims]

        all_events = user_events + tip_events + purchase_events + feedback_events + claim_events
        all_events.sort(key=lambda x: x['date'], reverse=True)
        
        return jsonify(all_events[:50])

@bp.route('/users', methods=['GET'])
@admin_only
def get_users():
    query = request.args.get('q', '').strip()[:100]  # Limit search length
    if not query or len(query) < 2:
        return jsonify([])  # Require at least 2 chars to search
    with get_session() as session:
        q = session.query(User)
        if query:
            q = q.filter(User.email.ilike(f"%{query}%") | User.username.ilike(f"%{query}%"))
        
        users = q.order_by(User.created_at.desc()).limit(50).all()
        return jsonify([{
            'id': u.id,
            'email': u.email,
            'username': u.username,
            'is_admin': u.is_admin,
            'disabled': u.disabled,
            'created_at': u.created_at
        } for u in users])

@bp.route('/actions', methods=['GET'])
@admin_only
def get_actions():
    with get_session() as session:
        pending_claims = session.query(ArtistClaim).filter(ArtistClaim.status == 'pending').all()
        claims_data = [{
            'id': c.id,
            'type': 'claim',
            'title': f"Artist Claim: {c.artist_id}",
            'description': f"User {c.user_id} wants to claim {c.artist_id}",
            'created_at': c.created_at
        } for c in pending_claims]
        
        # Example: Unread feedback could be added here if we had a status column
        
    return jsonify(claims_data)

@bp.route('/actions/claim/<int:claim_id>', methods=['POST'])
@admin_only
def handle_claim(claim_id):
    action = request.json.get('action') # approve, reject
    with get_session() as session:
        claim = session.query(ArtistClaim).get(claim_id)
        if not claim:
            return jsonify({'error': 'Claim not found'}), 404
            
        if action == 'approve':
            claim.status = 'verified'
            claim.verified_at = text("NOW()")
        elif action == 'reject':
            claim.status = 'rejected'
        else:
            return jsonify({'error': 'Invalid action'}), 400

        session.commit()
        log_audit(f'claim_{action}', 'claim', claim_id, {'claim_id': claim_id})
        return jsonify({'success': True})

@bp.route('/analytics/content-plays', methods=['GET'])
@admin_only
def get_content_plays():
    with get_session() as session:
        # We UNION ALL across Tracks, Shows, Videos, and Podcasts
        # Since not all have a "play_count" or "views" column that is reliably updated,
        # we will count from `play_history` or `listening_sessions` if we wanted to be super accurate.
        # But wait, ahoy uses `analytics_events` or `play_history`?
        # Let's check what's available. Tracks have `play_count`. Shows have `views`. Videos don't.
        # Let's just aggregate from `analytics_events` for anything not tracked, or use the columns.
        
        query = text('''
            SELECT 
                id, 
                title, 
                creator, 
                type, 
                SUM(plays) as total_plays
            FROM (
                -- 1. Tracks (use play_count column)
                SELECT 
                    track_id as id, 
                    title, 
                    artist as creator, 
                    'Track' as type, 
                    play_count as plays 
                FROM content_tracks 
                WHERE play_count > 0
                
                UNION ALL
                
                -- 2. Shows (use views column if it exists, Ahoy model has `views`)
                SELECT 
                    show_id as id, 
                    title, 
                    host as creator, 
                    'Show' as type, 
                    views as plays 
                FROM content_shows 
                WHERE views > 0
                
                UNION ALL
                
                -- 3. Calculate from play_history for anything else that might have it
                SELECT 
                    p.media_id as id,
                    COALESCE(t.title, s.title, v.title, pe.title, 'Unknown') as title,
                    COALESCE(t.artist, s.host, 'Ahoy', pe.show_slug, 'Unknown') as creator,
                    CASE 
                        WHEN p.media_type = 'track' THEN 'Track'
                        WHEN p.media_type = 'episode' THEN 'Podcast'
                        WHEN p.media_type = 'video' THEN 'Video'
                        WHEN p.media_type = 'show' THEN 'Show'
                        ELSE 'Media: ' || p.media_type
                    END as type,
                    1 as plays
                FROM play_history p
                LEFT JOIN content_tracks t ON p.media_id = t.track_id AND p.media_type = 'track'
                LEFT JOIN content_shows s ON p.media_id = s.show_id AND p.media_type = 'show'
                LEFT JOIN content_videos v ON p.media_id = v.video_id AND p.media_type = 'video'
                LEFT JOIN content_podcast_episodes pe ON p.media_id = pe.episode_id AND p.media_type = 'episode'
            ) as combined
            GROUP BY id, title, creator, type
            ORDER BY total_plays DESC
            LIMIT 200
        ''')
        
        results = session.execute(query).fetchall()
        
        data = [
            {
                'id': r[0],
                'title': r[1],
                'creator': r[2],
                'type': r[3],
                'plays': int(r[4]) if r[4] else 0
            }
            for r in results
        ]
        
        return jsonify(data)


@bp.route('/analytics/event', methods=['POST'])
def track_event():
    data = request.json
    if not data:
        return jsonify({'error': 'No data'}), 400

    ip = _get_client_ip()
    if ip is None:
        return jsonify({'ok': True})  # silently skip excluded IPs

    visitor_id, needs_cookie = _get_visitor_id()
    session_id = flask_session.get('session_id') or visitor_id

    with get_session() as session:
        event = AnalyticsEvent(
            user_id=current_user.id if current_user.is_authenticated else None,
            event_type=data.get('type', 'page_view'),
            path=data.get('path'),
            metadata_json=data.get('metadata'),
            session_id=session_id,
            ip_address=ip,
        )
        session.add(event)
        session.commit()
    response = jsonify({'ok': True})
    if needs_cookie:
        response.set_cookie(
            "ahoy_visitor_id",
            visitor_id,
            max_age=60 * 60 * 24 * 365,
            httponly=True,
            samesite="Lax",
            secure=request.is_secure,
        )
    return response

@bp.route('/heatmap', methods=['GET'])
@admin_only
def get_heatmap():
    # Aggregated page views by path
    with get_session() as session:
        # Group by path and count, filter by last 30 days
        # SQLAlchemy simplified grouping
        results = session.execute(text("""
            SELECT path, COUNT(*) as count 
            FROM analytics_events 
            WHERE event_type = 'page_view' 
            GROUP BY path 
            ORDER BY count DESC 
            LIMIT 50
        """)).fetchall()
        
        heatmap_data = [{'path': r[0], 'count': r[1]} for r in results]
        return jsonify(heatmap_data)

@bp.route('/analytics/visitors', methods=['GET'])
@admin_only
def get_visitors():
    with get_session() as session:
        total_unique = session.execute(text("""
            SELECT COUNT(DISTINCT ip_address)
            FROM analytics_events
            WHERE ip_address IS NOT NULL
        """)).scalar() or 0

        new_returning = session.execute(text("""
            SELECT
                SUM(CASE WHEN day_count = 1 THEN 1 ELSE 0 END) AS new_visitors,
                SUM(CASE WHEN day_count > 1 THEN 1 ELSE 0 END) AS returning_visitors
            FROM (
                SELECT ip_address, COUNT(DISTINCT DATE(created_at)) AS day_count
                FROM analytics_events
                WHERE ip_address IS NOT NULL
                GROUP BY ip_address
            ) sub
        """)).fetchone()

        top_ips = session.execute(text("""
            SELECT ip_address, COUNT(*) AS views, COUNT(DISTINCT path) AS unique_paths
            FROM analytics_events
            WHERE ip_address IS NOT NULL
              AND event_type = 'page_view'
              AND created_at >= NOW() - INTERVAL '30 days'
            GROUP BY ip_address
            ORDER BY views DESC
            LIMIT 10
        """)).fetchall()

        return jsonify({
            'total_unique': total_unique,
            'new_visitors': new_returning[0] if new_returning else 0,
            'returning_visitors': new_returning[1] if new_returning else 0,
            'top_ips': [{'ip': r[0], 'views': r[1], 'unique_paths': r[2]} for r in top_ips]
        })

@bp.route('/analytics/traffic', methods=['GET'])
@admin_only
def get_traffic():
    with get_session() as session:
        results = session.execute(text("""
            SELECT DATE(created_at) AS day, COUNT(*) AS views
            FROM analytics_events
            WHERE event_type = 'page_view'
              AND created_at >= NOW() - INTERVAL '30 days'
            GROUP BY DATE(created_at)
            ORDER BY day ASC
        """)).fetchall()
        return jsonify([{'date': str(r[0]), 'views': r[1]} for r in results])

@bp.route('/users/<int:user_id>/toggle_status', methods=['POST'])
@admin_only
def toggle_user_status(user_id):
    with get_session() as session:
        user = session.query(User).get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404

        # Prevent disabling self
        if user.id == current_user.id:
            return jsonify({'error': 'Cannot disable your own account'}), 400

        user.disabled = not user.disabled
        session.commit()

        status = "disabled" if user.disabled else "enabled"
    log_audit(f'user_{status}', 'user', user_id, {'email': user.email})
    return jsonify({'ok': True, 'status': status, 'disabled': user.disabled})

@bp.route('/users/export', methods=['GET'])
@admin_only
def export_users_csv():
    import csv
    import io
    from flask import make_response
    
    with get_session() as session:
        users = session.query(User).order_by(User.created_at.desc()).all()
        
        si = io.StringIO()
        cw = csv.writer(si)
        cw.writerow(['ID', 'Email', 'Username', 'Joined', 'Is Admin', 'Status', 'Wallet Balance'])
        
        for u in users:
            cw.writerow([
                u.id, 
                u.email, 
                u.username or '', 
                u.created_at.isoformat(), 
                'Yes' if u.is_admin else 'No',
                'Disabled' if u.disabled else 'Active',
                u.wallet_balance
            ])
            
        output = make_response(si.getvalue())
        output.headers["Content-Disposition"] = "attachment; filename=users_export.csv"
        output.headers["Content-type"] = "text/csv"
        return output

# ---------------------------------------------------------------------------
# Content CRUD (Tracks, Shows, Artists, Events, Merch, Videos, What's New)
# ---------------------------------------------------------------------------

CONTENT_MODEL_MAP = {
    'tracks': Track,
    'shows': Show,
    'artists': ContentArtist,
    'events': Event,
    'merch': ContentMerch,
    'videos': ContentVideo,
    'whats-new': WhatsNewItem,
    'studio_collections': StudioCollection,
    'podcast_shows': PodcastShow,
    'podcast_episodes': PodcastEpisode,
}

def _serialize_model(obj):
    """Simple serializer for SQLAlchemy models."""
    if obj is None:
        return None
    d = {}
    for column in obj.__table__.columns:
        val = getattr(obj, column.name)
        if isinstance(val, (datetime,)):
            d[column.name] = val.isoformat()
        elif hasattr(val, '__float__'): # Numeric, Float
            d[column.name] = float(val)
        else:
            d[column.name] = val
    return d

@bp.route('/upload/signed-url', methods=['POST'])
@login_required
@admin_only
def get_signed_url():
    import os
    data = request.get_json() or {}
    filename = data.get('filename')
    content_type = data.get('content_type')
    
    if not filename or not content_type:
        return jsonify({'error': 'filename and content_type are required'}), 400

    bucket_name = current_app.config.get('AHOY_GCS_BUCKET') or os.environ.get('AHOY_GCS_BUCKET', 'ahoy-dynamic-content')

    try:
        from google.cloud import storage
        from datetime import timedelta
        client = storage.Client()
        bucket = client.bucket(bucket_name)
        blob = bucket.blob(filename)
        
        url = blob.generate_signed_url(
            version="v4",
            expiration=timedelta(minutes=15),
            method="PUT",
            content_type=content_type,
        )
        
        public_url = f"https://storage.googleapis.com/{bucket_name}/{filename}"
        
        return jsonify({
            'signed_url': url,
            'public_url': public_url
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@bp.route('/content/<ctype>', methods=['GET'])
@admin_only
def list_content(ctype):
    model = CONTENT_MODEL_MAP.get(ctype)
    if not model:
        return jsonify({'error': 'Invalid content type'}), 400
    
    query = request.args.get('q', '')
    limit = min(int(request.args.get('limit', 50)), 100)
    offset = int(request.args.get('offset', 0))
    
    with get_session() as session:
        q = session.query(model)
        
        # Simple search based on common fields
        if query:
            if hasattr(model, 'title'):
                q = q.filter(model.title.ilike(f"%{query}%"))
            elif hasattr(model, 'name'):
                q = q.filter(model.name.ilike(f"%{query}%"))
        
        # Order by position if available, else ID desc
        if hasattr(model, 'position'):
            q = q.order_by(model.position.asc())
        else:
            q = q.order_by(model.id.desc())
            
        total = q.count()
        items = q.offset(offset).limit(limit).all()
        
        return jsonify({
            'items': [_serialize_model(i) for i in items],
            'total': total,
            'limit': limit,
            'offset': offset
        })

@bp.route('/content/<ctype>/<int:id>', methods=['GET'])
@admin_only
def get_content_item(ctype, id):
    model = CONTENT_MODEL_MAP.get(ctype)
    if not model:
        return jsonify({'error': 'Invalid content type'}), 400
        
    with get_session() as session:
        item = session.query(model).get(id)
        if not item:
            return jsonify({'error': 'Item not found'}), 404
        return jsonify(_serialize_model(item))

@bp.route('/content/<ctype>', methods=['POST'])
@admin_only
def create_content_item(ctype):
    model = CONTENT_MODEL_MAP.get(ctype)
    if not model:
        return jsonify({'error': 'Invalid content type'}), 400
        
    data = request.json
    if not data:
        return jsonify({'error': 'No data provided'}), 400
        
    with get_session() as session:
        # Create new instance and map fields
        item = model()
        for key, value in data.items():
            if hasattr(item, key) and key != 'id':
                setattr(item, key, value)
        
        session.add(item)
        session.commit()
        return jsonify({'ok': True, 'id': item.id, 'item': _serialize_model(item)})

@bp.route('/content/<ctype>/<int:id>', methods=['PUT'])
@admin_only
def update_content_item(ctype, id):
    model = CONTENT_MODEL_MAP.get(ctype)
    if not model:
        return jsonify({'error': 'Invalid content type'}), 400
        
    data = request.json
    if not data:
        return jsonify({'error': 'No data provided'}), 400
        
    with get_session() as session:
        item = session.query(model).get(id)
        if not item:
            return jsonify({'error': 'Item not found'}), 404
            
        for key, value in data.items():
            if hasattr(item, key) and key != 'id':
                setattr(item, key, value)
        
        session.commit()
        return jsonify({'ok': True, 'item': _serialize_model(item)})

@bp.route('/content/<ctype>/<int:id>', methods=['DELETE'])
@admin_only
def delete_content_item(ctype, id):
    model = CONTENT_MODEL_MAP.get(ctype)
    if not model:
        return jsonify({'error': 'Invalid content type'}), 400
        
    with get_session() as session:
        item = session.query(model).get(id)
        if not item:
            return jsonify({'error': 'Item not found'}), 404
            
        session.delete(item)
        session.commit()
        return jsonify({'ok': True})
@bp.route('/artists/stats', methods=['GET'])
@admin_only
def get_artist_stats():
    """Get list of all artists with aggregate earnings (tips + boosts). Supports search by name."""
    query = request.args.get('q', '').strip()
    with get_session() as session:
        # Fetch artists and their earnings
        # earnings = sum of tips + sum of boosts (purchases where type='boost' or 'tip')
        # Ahoy has a specific structure for this.
        
        sql = text("""
            SELECT
                a.id, a.name, a.image, a.payout_email,
                COALESCE((SELECT SUM(amount) FROM tips WHERE artist_id = a.artist_id), 0) +
                COALESCE((SELECT SUM(total) FROM purchases WHERE artist_id = a.artist_id AND type IN ('boost', 'tip') AND status = 'paid'), 0) as total_earnings
            FROM content_artists a
            WHERE (:q = '' OR a.name ILIKE :q_param)
            ORDER BY total_earnings DESC
            LIMIT 100
        """)
        
        results = session.execute(sql, {'q': query, 'q_param': f"%{query}%"}).fetchall()
        
        artists = [{
            'id': r[0],
            'name': r[1],
            'image': r[2],
            'payout_email': r[3],
            'earnings': float(r[4])
        } for r in results]
        
    return jsonify({'artists': artists})

@bp.route('/artists/<int:artist_id>/financials', methods=['GET'])
@admin_only
def get_artist_financials(artist_id):
    """Get detailed financial data for a specific artist (lifetime earnings, boost count, payout email)."""
    with get_session() as session:
        artist = session.query(ContentArtist).get(artist_id)
        if not artist:
            return jsonify({'error': 'Artist not found'}), 404

        # Lifetime earnings
        earnings_sql = text("""
            SELECT SUM(amount) FROM (
                SELECT amount FROM tips WHERE artist_id = :aid
                UNION ALL
                SELECT total as amount FROM purchases WHERE artist_id = :aid AND type IN ('boost', 'tip') AND status = 'paid'
            ) sub
        """)
        lifetime = session.execute(earnings_sql, {'aid': artist.artist_id}).scalar() or 0

        # Total boosts count
        boosts_count = session.query(Purchase).filter(
            Purchase.artist_id == artist.artist_id,
            Purchase.type == 'boost',
            Purchase.status == 'paid'
        ).count()
        
        return jsonify({
            'earnings': float(lifetime),
            'total_boosts': boosts_count,
            'payout_email': artist.payout_email,
            'stripe_account_id': getattr(artist, 'stripe_account_id', None)
        })
