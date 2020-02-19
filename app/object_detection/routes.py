from flask import render_template
from app.object_detection import bp
from flask_babel import _


@bp.route('/object_detection/', methods=['GET'])
@bp.route('/object_detection/index.html', methods=['GET'])
def index():
    return render_template('object_detection/index.html', title=_('Object_detection'))
