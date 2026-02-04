from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import URLSafeTimedSerializer
from flask import current_app
from app import db, login_manager

class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    profile_picture = db.Column(db.String(255), nullable=True)  # Filename of profile picture
    is_admin = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    claims = db.relationship('Claim', foreign_keys='Claim.user_id', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    reviewed_claims = db.relationship('Claim', foreign_keys='Claim.reviewed_by', backref='reviewer', lazy='dynamic')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_total_points(self):
        """Calculate total points from unique levels completed (one approved claim per level)."""
        # Get distinct level_ids with approved claims
        completed_level_ids = db.session.query(Claim.level_id.distinct()).filter(
            Claim.user_id == self.id,
            Claim.status == 'approved'
        ).all()

        # Sum the points from those levels
        if not completed_level_ids:
            return 0

        level_ids = [lid[0] for lid in completed_level_ids]
        total = db.session.query(db.func.sum(Level.points)).filter(
            Level.id.in_(level_ids)
        ).scalar()

        return total or 0

    def get_reset_token(self, expires_sec=1800):
        """Generate a password reset token that expires in 30 minutes (1800 seconds)."""
        serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
        return serializer.dumps(self.email, salt='password-reset-salt')

    @staticmethod
    def verify_reset_token(token, expires_sec=1800):
        """Verify the reset token and return the user if valid."""
        serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
        try:
            email = serializer.loads(token, salt='password-reset-salt', max_age=expires_sec)
        except:
            return None
        return User.query.filter_by(email=email).first()

    def __repr__(self):
        return f'<User {self.username}>'

class Level(db.Model):
    __tablename__ = 'levels'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text)
    difficulty = db.Column(db.String(20))
    rank = db.Column(db.Integer, nullable=True, unique=True)  # Rank 1-50, None for unranked
    points = db.Column(db.Integer, default=0, nullable=False)  # Auto-calculated as 51 - rank
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    claims = db.relationship('Claim', backref='level', lazy='dynamic')

    def update_points(self):
        """Update points based on rank (51 - rank for ranks 1-50, 0 for unranked)."""
        if self.rank and 1 <= self.rank <= 50:
            self.points = 51 - self.rank
        else:
            self.points = 0

    def __repr__(self):
        return f'<Level {self.name}>'

class Claim(db.Model):
    __tablename__ = 'claims'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    level_id = db.Column(db.Integer, db.ForeignKey('levels.id'), nullable=False, index=True)
    youtube_link = db.Column(db.String(255), nullable=False)
    user_notes = db.Column(db.Text)
    status = db.Column(db.String(20), default='pending', index=True)
    rank = db.Column(db.Integer, nullable=True)
    points = db.Column(db.Integer, default=0)
    is_first_victor = db.Column(db.Boolean, default=False, nullable=False)
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
    reviewed_at = db.Column(db.DateTime)
    reviewed_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    admin_notes = db.Column(db.Text)

    # Relationships

    def __repr__(self):
        return f'<Claim {self.id} by User {self.user_id} for Level {self.level_id}>'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
