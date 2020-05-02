from app.utils import print_lambda_timings#, invoke_lambda_function_synchronous
from flask import current_app as app
import json, base64
from io import BytesIO
from app import cache
import requests

@cache.memoize()
def get_prediction(modelname=None, image_bytes=None):
    if (image_bytes is None) or (modelname is None): return None
    coded_img = base64.b64encode(BytesIO(image_bytes).getvalue()).decode("utf-8")
    lambda_params = {'score_threshold': app.config.get('DETECTION_SCORE_THRESHOLD'),
                     'size': 800,
                     'model': modelname,
                     'data': coded_img}

    # TODO Change this
    # Experimental TorchScript quantized  MaskRCNN model
    if modelname == 'maskrcnn_quantized':
        r = requests.post('https://tuuka-maskrcnn-quant.ue.r.appspot.com/predict',
                          files={'file': image_bytes})
        r = json.loads(r.text)
    else:
        if app.config.get('LAMBDA_LOCAL'):
            from app.cvdemolambda import lambda_handler
            r = lambda_handler(lambda_params, None)
        else:
            # invokation via boto3 extension (AWS Credential and other params needed)
            '''
            r = invoke_lambda_function_synchronous('detectiononnxfunction',
                                               lambda_params,
                                               region_name=app.config.get('BOTO3_REGION'))
            r = json.load(r['Payload'])
            '''
            # Invoke through APIGateway
            r = requests.post(app.config.get('LAMBDA_URL'),
                              data=json.dumps(lambda_params).encode())
            r = json.loads(r.text)
        print_lambda_timings(r)

    data = json.loads(r['data'])
    pred = {
        'boxes' : data['boxes'],
        'labels' : data['labels'],
        'scores' : data['scores'],
        'colors' : data['colors'],
        'masks' : data.get('masks', None),
        'time' : None
    }

    timings = r.get('time', None)
    if timings is not None:
        pred['time'] = timings.get('all_time', None)

    # TODO Change this when models trained on other dataset will be added
    label_list = labels_coco_2017

    pred['labels'] = [label_list[pred['labels'][i]] for i in range(len(pred['labels']))]
    if pred['masks'] is not None:
        if (len(pred['masks']) > 0) and not ('data:image/jpeg;base64' in pred['masks']):
            pred['masks'] = f'data:image/jpeg;base64,{pred["masks"]}'
    return pred


labels_coco_2017 = ['background', 'person', 'bicycle', 'car', 'motorcycle', 'airplane',
    'bus', 'train', 'truck', 'boat', 'traffic light', 'fire hydrant', 'street sign',
    'stop sign', 'parking meter', 'bench', 'bird', 'cat', 'dog', 'horse', 'sheep',
    'cow', 'elephant', 'bear', 'zebra', 'giraffe', 'hat', 'backpack', 'umbrella',
    'shoe', 'eye glasses', 'handbag', 'tie', 'suitcase', 'frisbee', 'skis',
    'snowboard', 'sports ball', 'kite', 'baseball bat', 'baseball glove', 'skateboard',
    'surfboard', 'tennis racket', 'bottle', 'plate', 'wine glass', 'cup', 'fork',
    'knife', 'spoon', 'bowl', 'banana', 'apple', 'sandwich', 'orange', 'broccoli',
    'carrot', 'hot dog', 'pizza', 'donut', 'cake', 'chair', 'couch', 'potted plant',
    'bed', 'mirror', 'dining table', 'window', 'desk', 'toilet', 'door', 'tv',
    'laptop', 'mouse', 'remote', 'keyboard', 'cell phone', 'microwave', 'oven',
    'toaster', 'sink', 'refrigerator', 'blender', 'book', 'clock', 'vase', 'scissors',
    'teddy bear', 'hair drier', 'toothbrush', 'hair brush',
]
