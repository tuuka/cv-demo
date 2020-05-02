import json
import base64, requests
from flask import current_app as app
from app.utils import print_lambda_timings
from io import BytesIO
from app import cache
#from app.utils import invoke_lambda_function_synchronous

with open('app/static/imagenet_class_index.json') as json_file:
    imagenet_class = json.load(json_file)

@cache.memoize()
def get_prediction(modelname=None, image_bytes=None):
    if (image_bytes is None) or (modelname is None): return None
    coded_img = base64.b64encode(BytesIO(image_bytes).getvalue()).decode("utf-8")
    lambda_params = {'size': 224,
                     'model': modelname,
                     'data': coded_img,
                     'topN': 5}

    if app.config.get('LAMBDA_LOCAL'):
        from app.cvdemolambda import lambda_handler
        r = lambda_handler(lambda_params, None)
    else:
        # invokation via boto3 extension (AWS Credential and other params needed)
        '''
        r = invoke_lambda_function_synchronous('recognitiononnxfunction',
                                           lambda_params,
                                           region_name=app.config.get('BOTO3_REGION'))
        r = json.load(r['Payload'])
        '''

        # dont check config value correctness cause try-except in route
        r = requests.post(app.config.get('LAMBDA_URL'),
                          data=json.dumps(lambda_params).encode())
        r = json.loads(r.text)

    print_lambda_timings(r)
    data = json.loads(r['data'])
    predicted_idx = data['predicted_idx']
    predicted_score = data['predicted_scores']
    scores = [str(round(100 * s)) for s in predicted_score]
    obj_class = [imagenet_class[str(p)][0] for p in predicted_idx]
    obj_name = [imagenet_class[str(p)][1].replace('_', ' ') for p in predicted_idx]
    pred = {'scores': scores,
            'class': obj_class,
            'name': obj_name,
            'time': None}
    timings = r.get('time', None)
    if timings is not None:
        pred['time'] = timings.get('all_time', None)

    return pred
