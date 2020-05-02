from flask import render_template, jsonify, request
from app.image_recognition import bp, utils
import time
from flask_babel import _
from app.utils import print_memory
from flask import current_app as app


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
        print_memory()

        file = request.files.get('file')
        if not file:
            return jsonify({'error':'Not correct source img file'})

        t = time.time()
        file = file.read()

        try:
            prediction = utils.get_prediction(modelname=modelname, image_bytes=file)
        except Exception as e:
            app.logger.error('Error in get_prediction: {}.'.format(e))
            return jsonify({'error': 'Can not predict. Error: {}.'.format(e)})

        pred = {'error': ''}
        pred['prediction'] = prediction

        dt = time.time() - t  # get execution time
        app.logger.info(f'Recognition model prediction time: {dt:.02f} seconds')
        pred['time'] = round (dt, 2)
        return jsonify(pred)


