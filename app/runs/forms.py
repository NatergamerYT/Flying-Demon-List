from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, TextAreaField, SelectField, SubmitField, IntegerField, BooleanField
from wtforms.validators import DataRequired, URL, Length, Regexp, ValidationError, Optional, NumberRange
import re

class ClaimSubmissionForm(FlaskForm):
    level_name = StringField('Level Name', validators=[
        DataRequired(message='Please enter a level name'),
        Length(min=1, max=100, message='Level name must be between 1 and 100 characters')
    ])
    youtube_link = StringField('YouTube Link', validators=[
        DataRequired(message='YouTube link is required'),
        URL(message='Must be a valid URL'),
        Length(max=255, message='URL too long')
    ])
    user_notes = TextAreaField('Notes (Optional)', validators=[
        Length(max=500, message='Notes must be less than 500 characters')
    ])
    submit = SubmitField('Submit Claim')

    def validate_youtube_link(self, youtube_link):
        """Validate that the URL is a YouTube link."""
        url = youtube_link.data
        patterns = [
            r'(?:youtube\.com\/watch\?v=)([^&\s]+)',
            r'(?:youtu\.be\/)([^&\s]+)',
            r'(?:youtube\.com\/embed\/)([^&\s]+)'
        ]
        is_youtube = False
        for pattern in patterns:
            if re.search(pattern, url):
                is_youtube = True
                break

        if not is_youtube:
            raise ValidationError('Must be a valid YouTube link (youtube.com or youtu.be)')

class ReviewClaimForm(FlaskForm):
    action = SelectField('Action', choices=[
        ('approve', 'Approve'),
        ('reject', 'Reject')
    ], validators=[DataRequired()])
    is_first_victor = BooleanField('Mark as First Victor (only one per level)')
    admin_notes = TextAreaField('Admin Notes', validators=[
        Length(max=500, message='Notes must be less than 500 characters')
    ])
    submit = SubmitField('Submit Review')

class EditProfileForm(FlaskForm):
    username = StringField('Username', validators=[
        DataRequired(message='Username is required'),
        Length(min=3, max=64, message='Username must be between 3 and 64 characters'),
        Regexp(r'^[a-zA-Z0-9_]+$', message='Username can only contain letters, numbers, and underscores')
    ])
    profile_picture = FileField('Profile Picture', validators=[
        FileAllowed(['png', 'jpg', 'jpeg', 'gif'], 'Only PNG, JPG, JPEG, and GIF images are allowed')
    ])
    submit = SubmitField('Save Changes')
