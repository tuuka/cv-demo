from flask import Blueprint

bp = Blueprint('semantic_segmentation', __name__)

from . import routes
