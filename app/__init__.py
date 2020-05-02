from flask import Flask, request, current_app
from flask_caching import Cache
from flask_babel import Babel
from config import Config
from app import cli
#from app.boto3_extension import Boto3
from logging.config import dictConfig

dictConfig({
    'version': 1,
    'formatters': {'default': {
        'format': '[%(asctime)s] %(levelname)s in %(module)s: %(message)s',
    }},
    'handlers': {'wsgi': {
        'class': 'logging.StreamHandler',
        'stream': 'ext://flask.logging.wsgi_errors_stream',
        'formatter': 'default'
    }},
    'root': {
        'level': 'DEBUG' if Config.DEBUG else 'INFO',
        'handlers': ['wsgi']
    }
})

application = Flask(__name__)
application.config.from_object(Config)

babel = Babel(application)
cli.register(application)
#aws_boto = Boto3(application)
cache = Cache()
cache.init_app(application, config=application.config)

from app.errors import bp as errors_bp
from app.main import bp as main_bp
from app.image_recognition import bp as image_recognition_bp
from app.semantic_segmentation import bp as semantic_segmentation_bp
from app.object_detection import bp as object_detection_bp
application.register_blueprint(errors_bp)
application.register_blueprint(main_bp)
application.register_blueprint(image_recognition_bp)
application.register_blueprint(semantic_segmentation_bp)
application.register_blueprint(object_detection_bp)


@babel.localeselector
def get_locale():
    return request.accept_languages.best_match(current_app.config['LANGUAGES'])
