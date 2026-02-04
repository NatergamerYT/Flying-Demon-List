from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import current_user
from app.admin import admin_bp
from app.admin.decorators import admin_required
from app.claims.forms import ReviewClaimForm
from app.models import Claim, User, Level
from app import db
from datetime import datetime

@admin_bp.route('/dashboard')
@admin_required
def dashboard():
    """Admin dashboard overview."""
    pending_count = Claim.query.filter_by(status='pending').count()
    approved_count = Claim.query.filter_by(status='approved').count()
    rejected_count = Claim.query.filter_by(status='rejected').count()
    total_users = User.query.count()
    total_levels = Level.query.count()

    recent_claims = Claim.query.order_by(Claim.submitted_at.desc()).limit(10).all()

    stats = {
        'pending_count': pending_count,
        'approved_count': approved_count,
        'rejected_count': rejected_count,
        'total_users': total_users,
        'total_levels': total_levels
    }

    return render_template('admin/dashboard.html', stats=stats, recent_claims=recent_claims)

@admin_bp.route('/pending-claims')
@admin_required
def pending_claims():
    """View all pending claims."""
    claims = Claim.query.filter_by(status='pending')\
        .order_by(Claim.submitted_at.asc())\
        .all()

    return render_template('admin/pending_claims.html', claims=claims)

@admin_bp.route('/review/<int:claim_id>', methods=['GET', 'POST'])
@admin_required
def review_claim(claim_id):
    """Review a specific claim with rank assignment."""
    claim = Claim.query.get_or_404(claim_id)
    form = ReviewClaimForm()

    # Get level rank distribution for context
    from app.users.utils import get_level_rank_distribution, assign_rank_to_claim
    rank_info = get_level_rank_distribution(claim.level_id) if claim.level_id else None

    if form.validate_on_submit():
        action = form.action.data
        claim.admin_notes = form.admin_notes.data
        claim.reviewed_by = current_user.id
        claim.reviewed_at = datetime.utcnow()

        if action == 'approve':
            # Check if user already has an approved claim for this level
            existing_approved = Claim.query.filter_by(
                user_id=claim.user_id,
                level_id=claim.level_id,
                status='approved'
            ).filter(Claim.id != claim.id).first()

            if existing_approved:
                flash(f'User already has an approved claim (#{existing_approved.id}) for {claim.level.name}. Only one approved claim per level is allowed.', 'warning')
                return redirect(url_for('admin.review_claim', claim_id=claim_id))

            claim.status = 'approved'

            # Handle rank assignment
            new_rank = form.assigned_rank.data
            rank_success, rank_message = assign_rank_to_claim(claim, new_rank, current_user.id)
            if not rank_success:
                flash(rank_message, 'danger')
                # Don't commit, just redirect back
                return redirect(url_for('admin.review_claim', claim_id=claim_id))

            # Handle First Victor assignment
            is_first_victor = form.is_first_victor.data
            if is_first_victor:
                # Unset any existing First Victor for this level
                existing_first_victors = Claim.query.filter_by(
                    level_id=claim.level_id,
                    is_first_victor=True
                ).filter(Claim.id != claim.id).all()

                for existing in existing_first_victors:
                    existing.is_first_victor = False

                claim.is_first_victor = True
            else:
                claim.is_first_victor = False

            flash(f'Claim #{claim.id} approved!', 'success')
            if is_first_victor:
                flash(f'Marked as First Victor for {claim.level.name}.', 'info')
            if rank_message:
                flash(rank_message, 'info')

        elif action == 'reject':
            claim.status = 'rejected'
            claim.is_first_victor = False
            claim.rank = None
            claim.points = 0
            flash(f'Claim #{claim.id} has been rejected.', 'info')

        db.session.commit()
        return redirect(url_for('admin.pending_claims'))

    # Pre-populate form with current values if editing an already-reviewed claim
    if request.method == 'GET':
        form.assigned_rank.data = claim.rank
        if claim.is_first_victor:
            form.is_first_victor.data = True

    return render_template('admin/review_claim.html', claim=claim, form=form, rank_info=rank_info)

@admin_bp.route('/levels')
@admin_required
def levels():
    """Manage levels."""
    all_levels = Level.query.order_by(Level.name).all()
    return render_template('admin/levels.html', levels=all_levels)

@admin_bp.route('/level/add', methods=['POST'])
@admin_required
def add_level():
    """Add a new level."""
    name = request.form.get('name')
    description = request.form.get('description')
    difficulty = request.form.get('difficulty')
    rank = request.form.get('rank', type=int)

    if not name:
        flash('Level name is required.', 'danger')
        return redirect(url_for('admin.levels'))

    existing = Level.query.filter_by(name=name).first()
    if existing:
        flash('A level with this name already exists.', 'warning')
        return redirect(url_for('admin.levels'))

    # Validate rank if provided
    if rank is not None:
        if rank < 1 or rank > 50:
            flash('Rank must be between 1 and 50.', 'danger')
            return redirect(url_for('admin.levels'))

    # Create the level
    level = Level(name=name, description=description, difficulty=difficulty, rank=rank)
    db.session.add(level)
    db.session.flush()  # Get the level ID without committing

    # If rank is provided, shift other levels to make room
    if rank:
        levels_to_shift_down = Level.query.filter(
            Level.rank >= rank,
            Level.rank <= 50,
            Level.id != level.id
        ).order_by(Level.rank.asc()).all()

        for lvl in levels_to_shift_down:
            lvl.rank = lvl.rank + 1
            if lvl.rank > 50:
                lvl.rank = None
                lvl.update_points()
            else:
                lvl.update_points()

    level.update_points()  # Calculate points from rank
    db.session.commit()
    flash(f'Level "{name}" has been added (Rank: {rank or "unranked"}, Points: {level.points})!', 'success')
    return redirect(url_for('admin.levels'))

@admin_bp.route('/level/<int:level_id>/update-rank', methods=['POST'])
@admin_required
def update_level_rank(level_id):
    """Update a level's rank with cascading push logic."""
    level = Level.query.get_or_404(level_id)

    new_rank = request.json.get('rank')

    # Convert empty string or 'null' to None
    if new_rank in ['', 'null', None]:
        new_rank = None
    else:
        try:
            new_rank = int(new_rank)
            if not (1 <= new_rank <= 50):
                return jsonify({'success': False, 'message': 'Rank must be 1-50'}), 400
        except (ValueError, TypeError):
            return jsonify({'success': False, 'message': 'Invalid rank value'}), 400

    try:
        # If setting to unranked
        if new_rank is None:
            level.rank = None
            level.update_points()
            db.session.commit()
            return jsonify({
                'success': True,
                'message': f'Level "{level.name}" set to unranked',
                'new_rank': level.rank,
                'new_points': level.points
            })

        # Cascading push logic: build a chain of levels that need to move
        cascade_chain = []
        current_rank = new_rank

        # Build the chain of levels that will be displaced
        while current_rank <= 50:
            # Find the level currently at this rank (excluding the level being updated)
            displaced_level = Level.query.filter(
                Level.rank == current_rank,
                Level.id != level_id
            ).first()

            if displaced_level:
                # This level needs to be moved
                cascade_chain.append(displaced_level)
                current_rank += 1
            else:
                # Found an empty slot, stop cascading
                break

        # Apply the cascade: move each level in the chain to the next rank
        for displaced_level in reversed(cascade_chain):
            new_displaced_rank = displaced_level.rank + 1
            if new_displaced_rank > 50:
                # Pushed beyond rank 50, becomes unranked
                displaced_level.rank = None
            else:
                displaced_level.rank = new_displaced_rank
            displaced_level.update_points()


        level.rank = new_rank
        level.update_points()

        db.session.commit()

        affected_count = len(cascade_chain)
        if affected_count > 0:
            message = f'Level "{level.name}" updated to rank {new_rank}. {affected_count} level(s) shifted down.'
        else:
            message = f'Level "{level.name}" updated to rank {new_rank}'

        # Finally, assign the new rank to the target level

        return jsonify({
            'success': True,
            'message': message,
            'new_rank': level.rank,
            'new_points': level.points
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Error updating rank: {str(e)}'}), 500

@admin_bp.route('/level/<int:level_id>/delete', methods=['POST'])
@admin_required
def delete_level(level_id):
    """Delete a level."""
    level = Level.query.get_or_404(level_id)

    # Check if level has claims
    claim_count = Claim.query.filter_by(level_id=level_id).count()
    if claim_count > 0:
        flash(f'Cannot delete level with {claim_count} existing claims.', 'danger')
        return redirect(url_for('admin.levels'))

    db.session.delete(level)
    db.session.commit()
    flash(f'Level "{level.name}" has been deleted.', 'success')
    return redirect(url_for('admin.levels'))

@admin_bp.route('/users')
@admin_required
def users():
    """Manage users."""
    all_users = User.query.order_by(User.created_at.desc()).all()
    return render_template('admin/users.html', users=all_users)

@admin_bp.route('/user/<int:user_id>/delete', methods=['POST'])
@admin_required
def delete_user(user_id):
    """Delete a user and all their associated claims."""
    user = User.query.get_or_404(user_id)

    # Prevent deleting yourself
    if user.id == current_user.id:
        flash('You cannot delete your own account.', 'danger')
        return redirect(url_for('admin.users'))

    # Prevent deleting other admins
    if user.is_admin:
        flash('Cannot delete admin users.', 'danger')
        return redirect(url_for('admin.users'))

    username = user.username
    claim_count = user.claims.count()

    # Delete user (cascade will delete claims)
    db.session.delete(user)
    db.session.commit()

    # Note: Ranks are now manual, so deleted user's ranks create gaps that admins can fill manually

    flash(f'User "{username}" has been deleted along with {claim_count} claims.', 'success')
    return redirect(url_for('admin.users'))

@admin_bp.route('/user/<int:user_id>/toggle-admin', methods=['POST'])
@admin_required
def toggle_admin(user_id):
    """Toggle admin status for a user."""
    user = User.query.get_or_404(user_id)

    # Prevent modifying yourself
    if user.id == current_user.id:
        flash('You cannot modify your own admin status.', 'danger')
        return redirect(url_for('admin.users'))

    user.is_admin = not user.is_admin
    db.session.commit()

    status = 'granted' if user.is_admin else 'revoked'
    flash(f'Admin access {status} for user "{user.username}".', 'success')
    return redirect(url_for('admin.users'))

@admin_bp.route('/manage-ranks/<int:level_id>')
@admin_required
def manage_ranks(level_id):
    """Interface to manage all ranks within a level."""
    level = Level.query.get_or_404(level_id)

    # Get all approved claims for this level, ordered by current rank
    claims = Claim.query.filter_by(level_id=level_id, status='approved')\
        .order_by(Claim.rank.asc().nullslast(), Claim.submitted_at.asc())\
        .all()

    from app.users.utils import get_level_rank_distribution
    rank_info = get_level_rank_distribution(level_id)

    return render_template('admin/manage_ranks.html',
                         level=level,
                         claims=claims,
                         rank_info=rank_info)

@admin_bp.route('/update-rank/<int:claim_id>', methods=['POST'])
@admin_required
def update_rank(claim_id):
    """AJAX endpoint to update a claim's rank."""
    claim = Claim.query.get_or_404(claim_id)

    if claim.status != 'approved':
        return jsonify({'success': False, 'message': 'Can only rank approved claims'}), 400

    new_rank = request.json.get('rank')

    # Convert empty string or 'null' to None
    if new_rank in ['', 'null', None]:
        new_rank = None
    else:
        try:
            new_rank = int(new_rank)
            if not (1 <= new_rank <= 50):
                return jsonify({'success': False, 'message': 'Rank must be 1-50'}), 400
        except (ValueError, TypeError):
            return jsonify({'success': False, 'message': 'Invalid rank value'}), 400

    from app.users.utils import assign_rank_to_claim
    success, message = assign_rank_to_claim(claim, new_rank, current_user.id)

    if success:
        return jsonify({
            'success': True,
            'message': message,
            'new_rank': claim.rank,
            'new_points': claim.points
        })
    else:
        return jsonify({'success': False, 'message': message}), 400

@admin_bp.route('/toggle-first-victor/<int:claim_id>', methods=['POST'])
@admin_required
def toggle_first_victor(claim_id):
    """AJAX endpoint to toggle First Victor status for a claim."""
    claim = Claim.query.get_or_404(claim_id)

    if claim.status != 'approved':
        return jsonify({'success': False, 'message': 'Can only assign First Victor to approved claims'}), 400

    is_first_victor = request.json.get('is_first_victor', False)

    if is_first_victor:
        # Unset any existing First Victor for this level
        existing_first_victors = Claim.query.filter_by(
            level_id=claim.level_id,
            is_first_victor=True
        ).filter(Claim.id != claim.id).all()

        for existing in existing_first_victors:
            existing.is_first_victor = False

        claim.is_first_victor = True
        message = f'Claim #{claim.id} marked as First Victor for {claim.level.name}'
    else:
        claim.is_first_victor = False
        message = f'First Victor status removed from claim #{claim.id}'

    db.session.commit()

    return jsonify({
        'success': True,
        'message': message,
        'is_first_victor': claim.is_first_victor
    })
