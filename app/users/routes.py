from flask import render_template, abort, redirect, url_for, flash, request, current_app
from flask_login import current_user, login_required
from werkzeug.utils import secure_filename
import os
from app.users import users_bp
from app.models import User, Claim, Level
from app.claims.forms import EditProfileForm
from collections import defaultdict

@users_bp.route('/<username>')
def profile(username):
    """Display user profile with claims grouped by level."""
    user = User.query.filter_by(username=username).first_or_404()

    # Get all user's claims
    claims = Claim.query.filter_by(user_id=user.id).all()

    # Group claims by level
    claims_by_level = defaultdict(list)
    for claim in claims:
        claims_by_level[claim.level.name].append(claim)

    # Sort claims within each level by status and submission date
    for level_name in claims_by_level:
        claims_by_level[level_name].sort(
            key=lambda c: (c.status != 'approved', c.submitted_at),
            reverse=True
        )

    # Sort levels by name
    sorted_levels = sorted(claims_by_level.items())

    # Calculate statistics
    approved_claims = [c for c in claims if c.status == 'approved']
    total_points = user.get_total_points()
    completed_levels = len(set(c.level_id for c in approved_claims))
    first_victor_count = len([c for c in approved_claims if c.is_first_victor])

    stats = {
        'total_points': total_points,
        'total_claims': len(claims),
        'approved_count': len(approved_claims),
        'pending_count': len([c for c in claims if c.status == 'pending']),
        'rejected_count': len([c for c in claims if c.status == 'rejected']),
        'completed_levels': completed_levels,
        'first_victor_count': first_victor_count
    }

    return render_template('users/profile.html', user=user, claims_by_level=sorted_levels, stats=stats)

@users_bp.route('/edit-profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    """Allow users to edit their profile, including uploading a profile picture."""
    form = EditProfileForm()
    if form.validate_on_submit():
        # Check if username is being changed and if it's available
        if form.username.data != current_user.username:
            existing_user = User.query.filter_by(username=form.username.data).first()
            if existing_user:
                flash('Username already taken. Please choose a different one.', 'danger')
                return redirect(url_for('users.edit_profile'))
            current_user.username = form.username.data

        # Handle profile picture upload
        if form.profile_picture.data:
            filename = secure_filename(form.profile_picture.data.filename)
            filepath = os.path.join(current_app.root_path, 'static', 'uploads', filename)
            form.profile_picture.data.save(filepath)
            current_user.profile_picture = filename

        # Save changes
        from app import db
        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('users.profile', username=current_user.username))

    # Pre-populate form
    form.username.data = current_user.username
    return render_template('users/edit_profile.html', form=form)
