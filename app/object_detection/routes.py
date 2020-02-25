from flask import render_template, request, jsonify
from app.object_detection import bp, utils
from flask_babel import _


@bp.route('/object_detection/', methods=['GET'])
@bp.route('/object_detection/index.html', methods=['GET'])
def index():
    return render_template('object_detection/index.html', title=_('Object_detection'))


@bp.route('/object_detection/predict', methods=['POST'])
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
        return jsonify({'error':'', 'prediction':prediction})
