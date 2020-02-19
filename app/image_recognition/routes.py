from flask import render_template
from app.image_recognition import bp
from flask_babel import _


@bp.route('/image_recognition/', methods=['GET', 'POST'])
@bp.route('/image_recognition/index.html', methods=['GET', 'POST'])
def index():
    return render_template('image_recognition/index.html', title=_('Image recognition'))

