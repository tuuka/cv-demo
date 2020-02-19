from flask import Blueprint

bp = Blueprint('object_detection', __name__)

from . import routes
