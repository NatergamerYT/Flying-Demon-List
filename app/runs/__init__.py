from flask import Blueprint

claims_bp = Blueprint('claims', __name__)

from app.claims import routes
