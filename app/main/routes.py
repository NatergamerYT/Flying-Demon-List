from flask import render_template, request
from app.main import main_bp
from app.models import Claim, Level, User
from app import db
from sqlalchemy.exc import OperationalError
from flask import jsonify
import re

def get_youtube_video_id(url):
    """Extract YouTube video ID from URL."""
    if not url:
        return None
    match = re.search(r'(?:youtube\.com/watch\?v=|youtu\.be/)([a-zA-Z0-9_-]{11})', url)
    return match.group(1) if match else None

@main_bp.route('/')
def index():
    """Homepage with hardest levels."""
    # Get levels ordered by rank (1 at top, 50 at bottom, unranked at bottom)
    try:
        hardest_levels = Level.query.order_by(
            Level.rank.asc().nullslast(),
            Level.name
        ).all()
    except OperationalError:
        # If the `levels` table doesn't exist (e.g. migrations not applied),
        # return an empty homepage without raising a 500.
        hardest_levels = []

    # Add video ID and victors for each level
    for level in hardest_levels:
        approved_claims = level.claims.filter_by(status='approved').order_by(Claim.submitted_at).all()
        level.video_id = get_youtube_video_id(approved_claims[0].youtube_link) if approved_claims else None
        level.first_victor = approved_claims[0].user if approved_claims else None
        level.other_victors = [claim.user for claim in approved_claims[1:]]

    try:
        total_claims = Claim.query.filter_by(status='approved').count()
        total_users = User.query.count()
        total_levels = Level.query.count()
    except OperationalError:
        total_claims = 0
        total_users = 0
        total_levels = 0

    stats = {
        'total_claims': total_claims,
        'total_users': total_users,
        'total_levels': total_levels
    }

    return render_template('index.html', hardest_levels=hardest_levels, stats=stats)

@main_bp.route('/leaderboard')
def leaderboard():
    """Leaderboard showing users ranked by cumulative score."""
    # Get all users with at least one approved claim
    # Explicitly specify join condition since Claim has two foreign keys to User
    users_with_claims = User.query.join(Claim, User.id == Claim.user_id).filter(Claim.status == 'approved').distinct().all()

    # Build user leaderboard data
    user_rankings = []
    for user in users_with_claims:
        total_points = user.get_total_points()
        completed_levels = Claim.query.filter_by(
            user_id=user.id,
            status='approved'
        ).distinct(Claim.level_id).count()

        # Count First Victor badges
        first_victor_count = Claim.query.filter_by(
            user_id=user.id,
            is_first_victor=True,
            status='approved'
        ).count()

        user_rankings.append({
            'user': user,
            'total_points': total_points,
            'completed_levels': completed_levels,
            'first_victor_count': first_victor_count
        })

    # Sort by total points (descending)
    user_rankings.sort(key=lambda x: x['total_points'], reverse=True)

    return render_template('leaderboard/index.html', user_rankings=user_rankings)


@main_bp.route('/health')
def health():
    """Simple health check endpoint verifying DB connectivity."""
    try:
        # perform a lightweight query
        db.session.execute('SELECT 1')
        return jsonify(status='ok'), 200
    except Exception:
        return jsonify(status='error'), 500
