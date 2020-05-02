from flask import render_template, jsonify, request
from flask import current_app as app
from app.object_detection import bp, utils
from flask_babel import _
import time
from app.utils import print_memory


@bp.route('/object_detection/', methods=['GET', 'POST'])
@bp.route('/object_detection/index.html', methods=['GET', 'POST'])
def index():
    return render_template('object_detection/index.html', title=_('Object_detection'))


@bp.route('/object_detection/predict', endpoint= '/object_detection/predict', methods=['POST'])
def predict():
    if request.method == 'POST':
        if 'file' not in request.files:
            return jsonify({'error':'No source img file'})
        modelname = request.args.get('model', None)
        #print_memory()
        file = request.files.get('file')
        if not file:
            return jsonify({'error':'Not correct source img file'})

        t = time.time()
        file = file.read()

        try:
            prediction = utils.get_prediction(modelname=modelname,
                                              image_bytes=file)
        except Exception as e:
            app.logger.error('Error in get_prediction: {}.'.format(e))
            return jsonify({'error': 'Can not predict. Error: {}.'.format(e)})

        dt = time.time() - t
        app.logger.info(f'Detection model prediction time: {dt:.02f} seconds')
        return jsonify({'error':'', 'prediction':prediction, 'time': round(dt,2)})
