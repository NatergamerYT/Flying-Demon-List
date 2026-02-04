from flask import render_template, request
from app.main import main_bp
from app.models import Claim, Level, User
from app import db
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
    hardest_levels = Level.query.order_by(
        Level.rank.asc().nullslast(),
        Level.name
    ).all()

    # Add video ID and victors for each level
    for level in hardest_levels:
        approved_claims = level.claims.filter_by(status='approved').order_by(Claim.submitted_at).all()
        level.video_id = get_youtube_video_id(approved_claims[0].youtube_link) if approved_claims else None
        level.first_victor = approved_claims[0].user if approved_claims else None
        level.other_victors = [claim.user for claim in approved_claims[1:]]

    total_claims = Claim.query.filter_by(status='approved').count()
    total_users = User.query.count()
    total_levels = Level.query.count()

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
