import os
import click
from app import create_app, db
from app.models import User, Level

app = create_app(os.getenv('FLASK_ENV') or 'development')

@app.cli.command()
@click.option('--username', prompt=True)
@click.option('--email', prompt=True)
@click.option('--password', prompt=True, hide_input=True, confirmation_prompt=True)
def create_admin(username, email, password):
    """Create an admin user."""
    if User.query.filter((User.username == username) | (User.email == email)).first():
        click.echo(f'Error: A user with username "{username}" or email "{email}" already exists.', err=True)
        return
    user = User(username=username, email=email, is_admin=True)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    click.echo(f'Admin user {username} created successfully!')

@app.cli.command()
def seed_levels():
    """Seed initial game levels."""
    levels = [
        {'name': 'Level 1 - Tutorial', 'description': 'Learn the basics', 'difficulty': 'Easy'},
        {'name': 'Level 2 - Getting Started', 'description': 'Apply your skills', 'difficulty': 'Easy'},
        {'name': 'Level 3 - Intermediate Challenge', 'description': 'Test your abilities', 'difficulty': 'Medium'},
        {'name': 'Level 4 - Advanced Tactics', 'description': 'Master complex mechanics', 'difficulty': 'Medium'},
        {'name': 'Level 5 - Expert Trial', 'description': 'Push your limits', 'difficulty': 'Hard'},
        {'name': 'Level 6 - Nightmare Mode', 'description': 'Only for the best', 'difficulty': 'Hard'},
    ]
    for level_data in levels:
        existing = Level.query.filter_by(name=level_data['name']).first()
        if not existing:
            level = Level(**level_data)
            db.session.add(level)
    db.session.commit()
    click.echo('Levels seeded successfully!')

if __name__ == '__main__':
    app.run()
