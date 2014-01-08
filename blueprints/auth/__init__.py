__author__ = 'zifnab'
from flask import Blueprint, current_app
from flask_login import LoginManager
from blueprints.auth.models import User
blueprint = Blueprint('auth', __name__, template_folder='templates')

from views import login, register

login_manager = LoginManager(current_app)

@login_manager.user_loader
def load_user(user_id):
    return User.objects(username__iexact=user_id).first()


