from flask import render_template, jsonify, request
from flask import current_app as app
from app.semantic_segmentation import bp, utils
from flask_babel import _
import time
from app.utils import print_memory



@bp.route('/semantic_segmentation/', methods=['GET', 'POST'])
@bp.route('/semantic_segmentation/index.html', methods=['GET', 'POST'])
def index():
    return render_template('semantic_segmentation/index.html', title=_('Semantic segmentation'))


@bp.route('/semantic_segmentation/predict', methods=['POST'])
def predict():
    if request.method == 'POST':
        if 'file' not in request.files:
            return jsonify({'error':'No source img file'})
        modelname = request.args.get('model', None)
        print_memory()
        file = request.files.get('file')
        if not file:
            return jsonify({'error':'Not correct source img file'})

        t = time.time()
        file = file.read()

        try:
            prediction = utils.get_prediction(modelname=modelname,
                                                           image_bytes=file)
        except Exception as e:
            app.logger.error(f'Error in get_prediction: {e}.')
            return jsonify({'error': f'Can not predict. Exception: {e}.'})

        pred = {'error': '',
                'prediction' : prediction
                }
        dt = time.time() - t
        app.logger.info(f'Segmentation model prediction time: {dt:.02f} seconds')
        pred['time'] = round(dt, 2)
        return jsonify(pred)
