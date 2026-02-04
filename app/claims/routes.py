from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app.claims import claims_bp
from app.claims.forms import ClaimSubmissionForm
from app.models import Claim, Level
from app import db
from datetime import datetime

@claims_bp.route('/submit', methods=['GET', 'POST'])
@login_required
def submit():
    """Submit a new claim."""
    form = ClaimSubmissionForm()

    # Get existing levels for autocomplete
    existing_levels = Level.query.order_by(Level.name).all()

    if form.validate_on_submit():
        level_name = form.level_name.data.strip()

        # Check if level exists, create if not
        level = Level.query.filter_by(name=level_name).first()
        if not level:
            level = Level(name=level_name)
            db.session.add(level)
            db.session.flush()  # Get the level ID

        claim = Claim(
            user_id=current_user.id,
            level_id=level.id,
            youtube_link=form.youtube_link.data,
            user_notes=form.user_notes.data
        )
        db.session.add(claim)
        db.session.commit()
        flash('Your claim has been submitted and is pending admin approval!', 'success')
        return redirect(url_for('claims.my_claims'))

    return render_template('claims/submit.html', title='Submit Claim', form=form, existing_levels=existing_levels)

@claims_bp.route('/my-claims')
@login_required
def my_claims():
    """View current user's claims."""
    user_claims = Claim.query.filter_by(user_id=current_user.id)\
        .order_by(Claim.submitted_at.desc())\
        .all()

    return render_template('claims/my_claims.html', claims=user_claims)

# Voting system removed - ranks are now manually assigned by admins
