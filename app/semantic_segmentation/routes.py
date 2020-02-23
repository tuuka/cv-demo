from flask import render_template, request, jsonify
from app.semantic_segmentation import bp, utils
from flask_babel import _

@bp.route('/semantic_segmentation/', methods=['GET'])
@bp.route('/semantic_segmentation/index.html', methods=['GET'])
def index():
    return render_template('semantic_segmentation/index.html', title=_('Semantic segmentation'))


@bp.route('/semantic_segmentation/predict', methods=['POST'])
def predict():
    if request.method == 'POST':
        if 'file' not in request.files:
            return jsonify({'error':'No source img file'})
        modelname = request.args.get('model', None)
        file = request.files.get('file')
        if not file:
            return jsonify({'error':'Not correct source img file'})
        file = file.read()
        prediction, classes_map = utils.get_prediction(modelname=modelname, image_bytes=file)
        pred = {'error': ''}
        pred['prediction'] = prediction
        pred['classes_map'] = classes_map
        return jsonify(pred)
