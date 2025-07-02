from flask import Blueprint

bp = Blueprint('api', __name__)

# Import the modules to register their routes
from app.api import users, friends, admin, online 