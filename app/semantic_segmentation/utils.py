import base64
import json
from io import BytesIO
import requests
from flask import current_app as app
from app import cache
from app.utils import print_lambda_timings


@cache.memoize()
def get_prediction(modelname=None, image_bytes=None):
    if (image_bytes is None) or (modelname is None): return None
    coded_img = base64.b64encode(BytesIO(image_bytes).getvalue()).decode("utf-8")
    labels = labels_pascal
    lambda_params = {'size': 600,
                     'model': modelname,
                     'data': coded_img,
                     'labels': labels,
                     'topN': 10}

    if app.config.get('LAMBDA_LOCAL'):
        from app.cvdemolambda import lambda_handler
        r = lambda_handler(lambda_params, None)
    else:
        # dont check config value correctness cause try-except in route
        r = requests.post(app.config.get('LAMBDA_URL'),
                          data=json.dumps(lambda_params).encode())
        r = json.loads(r.text)

    print_lambda_timings(r)
    data = json.loads(r['data'])

    img_seg = data['img_seg']
    classes_in_image = data['classes']
    img_seg = 'data:image/jpeg;base64,' + img_seg
    pred = {'img_seg': img_seg, 'classes': classes_in_image, 'time': None}
    timings = r.get('time', None)
    if timings is not None:
        pred['time'] = timings.get('all_time', None)
    return pred


labels_pascal = ['background', 'aeroplane', 'bicycle', 'bird', 'boat', 'bottle', 'bus',
                 'car', 'cat', 'chair', 'cow', 'dining table', 'dog', 'horse', 'motorbike',
                 'person', 'potted plant', 'sheep', 'sofa', 'train', 'tv/monitor']

labels_ade20k = ['wall',
                 'building',
                 'sky',
                 'floor',
                 'tree',
                 'ceiling',
                 'road',
                 'bed',
                 'window ',
                 'grass',
                 'cabinet',
                 'sidewalk',
                 'person',
                 'ground',
                 'door',
                 'table',
                 'mountain',
                 'vegetation',
                 'curtain',
                 'chair',
                 'car',
                 'water',
                 'painting, picture',
                 'sofa',
                 'shelf',
                 'house',
                 'sea',
                 'mirror',
                 'rug, carpeting',
                 'field',
                 'armchair',
                 'seat',
                 'fence, fencing',
                 'desk',
                 'rock, stone',
                 'wardrobe, closet',
                 'lamp',
                 'bathtub',
                 'railing, rail',
                 'cushion',
                 'base, pedestal',
                 'box',
                 'column, pillar',
                 'signboard, sign',
                 'chest of drawers',
                 'counter',
                 'sand',
                 'sink',
                 'skyscraper',
                 'fireplace, hearth',
                 'refrigerator, icebox',
                 'grandstand, covered stand',
                 'path',
                 'stairs, steps',
                 'runway',
                 'display case, vitrine',
                 'billiard table',
                 'pillow',
                 'screen door',
                 'stairway',
                 'river',
                 'bridge',
                 'bookcase',
                 'blind, screen',
                 'coffee table',
                 'toilet, crapper',
                 'flower',
                 'book',
                 'hill',
                 'bench',
                 'countertop',
                 'cooking stove',
                 'palm tree',
                 'kitchen island',
                 'computer',
                 'swivel chair',
                 'boat',
                 'bar',
                 'arcade machine',
                 'hovel, hut',
                 'bus',
                 'towel',
                 'light source',
                 'truck',
                 'tower',
                 'chandelier',
                 'awning, sunshade',
                 'streetlight',
                 'booth, cubicle, kiosk',
                 'tv set',
                 'airplane',
                 'dirt track',
                 'apparel',
                 'pole',
                 'land, ground, soil',
                 'banister',
                 'escalator',
                 'ottoman, pouf',
                 'bottle',
                 'buffet, counter, sideboard',
                 'poster',
                 'stage',
                 'van',
                 'ship',
                 'fountain',
                 'conveyor belt',
                 'canopy',
                 'washing machine',
                 'plaything, toy',
                 'swimming pool',
                 'stool',
                 'barrel, cask',
                 'basket',
                 'waterfall',
                 'tent',
                 'bag',
                 'motorbike',
                 'cradle',
                 'oven',
                 'ball',
                 'food',
                 'step, stair',
                 'tank',
                 'trade name, brand name',
                 'microwave oven',
                 'flowerpot',
                 'animal',
                 'bicycle',
                 'lake',
                 'dishwashing machine',
                 'projection screen',
                 'blanket',
                 'sculpture',
                 'exhaust hood',
                 'sconce',
                 'vase',
                 'traffic light',
                 'tray',
                 'trash can',
                 'fan',
                 'pier, wharf',
                 'crt screen',
                 'plate',
                 'monitor',
                 'bulletin board',
                 'shower',
                 'radiator',
                 'drinking glass',
                 'clock',
                 'flag']
