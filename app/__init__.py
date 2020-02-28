from flask import Flask, request, current_app
from config import Config
from flask_babel import Babel


application = Flask(__name__)
application.config.from_object(Config)
babel = Babel(application)

from app.main import bp as main_bp
from app.image_recognition import bp as image_recognition_bp
from app.semantic_segmentation import bp as semantic_segmentation_bp
from app.object_detection import bp as object_detection_bp
application.register_blueprint(main_bp)
application.register_blueprint(image_recognition_bp)
application.register_blueprint(semantic_segmentation_bp)
application.register_blueprint(object_detection_bp)


@babel.localeselector
def get_locale():
    return request.accept_languages.best_match(current_app.config['LANGUAGES'])
