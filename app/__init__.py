from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect
from config import config
from .utils import extract_youtube_id
from sqlalchemy import inspect
from flask_migrate import upgrade
import os

db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()
csrf = CSRFProtect()

def create_app(config_name='development'):
    app = Flask(__name__)
    app.config.from_object(config[config_name])

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)

    # Configure login manager
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'

    # Register custom template filters
    @app.template_filter('youtube_id')
    def youtube_id_filter(url):
        return extract_youtube_id(url)

    # Register blueprints
    from app.auth import auth_bp
    from app.main import main_bp
    from app.claims import claims_bp
    from app.users import users_bp
    from app.admin import admin_bp

    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(main_bp)
    app.register_blueprint(claims_bp, url_prefix='/claims')
    app.register_blueprint(users_bp, url_prefix='/user')
    app.register_blueprint(admin_bp, url_prefix='/admin')

    # Error handlers
    @app.errorhandler(404)
    def not_found_error(error):
        from flask import render_template
        return render_template('errors/404.html'), 404

    @app.errorhandler(403)
    def forbidden_error(error):
        from flask import render_template
        return render_template('errors/403.html'), 403

    @app.errorhandler(500)
    def internal_error(error):
        from flask import render_template
        db.session.rollback()
        return render_template('errors/500.html'), 500

    # Ensure tables and migrations are applied on startup. This helps fresh
    # deployments (e.g., Render) that don't run `flask db upgrade` automatically.
    try:
        with app.app_context():
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()
            if 'levels' not in tables:
                # Try running migrations first; fall back to create_all().
                try:
                    upgrade()
                except Exception:
                    db.create_all()

            # Optionally create a default admin user when requested via env var.
            if os.environ.get('AUTO_CREATE_ADMIN', '0') == '1':
                # Import here to avoid circular import during module load
                from app.models import User
                admin_exists = User.query.filter_by(is_admin=True).first()
                if not admin_exists:
                    username = os.environ.get('ADMIN_USERNAME', 'NaterGamer')
                    email = os.environ.get('ADMIN_EMAIL', 'natergamer@example.com')
                    password = os.environ.get('ADMIN_PASSWORD', 'Nc522774')
                    user = User(username=username, email=email, is_admin=True)
                    user.set_password(password)
                    db.session.add(user)
                    db.session.commit()
    except Exception:
        # If creation/migration fails, allow the app to start and surface errors.
        pass

    return app

