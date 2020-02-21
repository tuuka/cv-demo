from flask import render_template, request, jsonify
from app.image_recognition import bp, utils
from flask_babel import _


@bp.route('/image_recognition/', methods=['GET', 'POST'])
@bp.route('/image_recognition/index.html', methods=['GET', 'POST'])
def index():
    return render_template('image_recognition/index.html', title=_('Image recognition'))


@bp.route('/image_recognition/predict', methods=['POST'])
def predict():
    if request.method == 'POST':
        if 'file' not in request.files:
            return jsonify({'error':'No source img file'})
        modelname = request.args.get('model', None)
        file = request.files.get('file')
        if not file:
            return jsonify({'error':'Not correct source img file'})
        file = file.read()

        prediction = utils.get_prediction(modelname=modelname, image_bytes=file)
        pred = {'error': ''}
        pred['prediction'] = prediction
        return jsonify(pred)