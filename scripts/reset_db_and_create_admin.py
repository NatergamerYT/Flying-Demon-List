from app import create_app, db
from app.models import User
import os

def reset_and_create_admin():
    app = create_app(os.getenv('FLASK_ENV') or 'development')
    with app.app_context():
        print('Dropping all tables...')
        db.drop_all()
        print('Recreating all tables...')
        db.create_all()

        username = 'NaterGamer'
        email = 'natergamer@example.com'
        password = 'Nc522774'

        existing = User.query.filter((User.username == username) | (User.email == email)).first()
        if existing:
            print('Existing user found, deleting...')
            db.session.delete(existing)
            db.session.commit()

        user = User(username=username, email=email, is_admin=True)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        print(f'Admin user "{username}" created with email {email}.')

if __name__ == '__main__':
    reset_and_create_admin()
