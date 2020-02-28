from flask import render_template, g, jsonify, request
from app.main import bp
from flask_babel import _, get_locale
from app.translate import translate, detect_language


@bp.before_app_request
def before_request():
    g.locale = str(get_locale())


@bp.route('/', methods=['GET', 'POST'])
@bp.route('/index', methods=['GET', 'POST'])
def index():
    return render_template('index.html', title=_('Home'))


@bp.route('/translate', methods=['POST'])
def translate_text():
    return jsonify({'text': translate(request.form['text'],
                                      request.form['source_language'],
                                      request.form['dest_language'])})

@bp.route('/lgdetect', methods=['POST'])
def lgdetect():
    return jsonify({'lg': detect_language(request.form['text'])})