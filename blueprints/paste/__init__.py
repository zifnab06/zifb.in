__author__ = 'zifnab'
from flask import Blueprint
blueprint = Blueprint("paste", __name__, template_folder="templates")

from views import main

