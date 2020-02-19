from flask import Blueprint

bp = Blueprint('image_recognition', __name__)

from . import routes

