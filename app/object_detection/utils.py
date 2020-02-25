import io, base64, torch, torchvision
from flask import current_app
from app.object_detection import models
from app.utils import random_colors
from PIL import Image


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
    'teddy bear', 'hair drier', 'toothbrush', 'hair brush']


def get_prediction(modelname=None, image_bytes=None):
    if (image_bytes is None) or (modelname is None): return None
    img = Image.open(io.BytesIO(image_bytes)).convert('RGB')
    orig_size = img.size
    img = torchvision.transforms.ToTensor()(img)
    model = models.model_load(modelname)

    # to make boxes' coordinates relative
    XYXY = list(img.size())[1:][::-1]
    XYXY = torch.tensor(XYXY + XYXY).float()

    labels = labels_coco_2017

    # reduce size of image proccessed by model if needed
    # model.transform.max_size = 640
    # model.transform.min_size = (480,)

    with torch.no_grad():
        model.eval()
        prediction = model([img])[0]

    pred = {
        'boxes'  : [],
        'labels' : [],
        'colors' : [],
        'scores': [],
        'orig_size' : list(orig_size)
    }

    N = len(prediction['scores'][prediction['scores'] > current_app.config['DETECTION_SCORE_THRESHOLD']])
    pred['colors'] = random_colors(N)

    # Take TopN scores prediction and convert all to list cause
    # tensor is not JSON serializable
    for i in range(N):
        pred['boxes'].append((prediction['boxes'][i].cpu() / XYXY).tolist())
        pred['labels'].append(labels[prediction['labels'][i]])
        pred['scores'].append(prediction['scores'][i].item())

    # making color mask for instance segmentation by putting objects with high scores above objects with less scores
    if (prediction.get('masks') is not None) & (len(prediction['masks'])>0):
        r = torch.zeros_like(prediction['masks'][0]).byte()
        g = torch.zeros_like(prediction['masks'][0]).byte()
        b = torch.zeros_like(prediction['masks'][0]).byte()
        # backwise order to order masks according scores
        for i in range(len(pred['boxes']))[::-1]:
            mask = (prediction['masks'][i] > 0.5)
            # converting hex to rgb ..
            r[mask], g[mask], b[mask] = tuple(int(pred['colors'][i][j:j+2], 16) for j in (1, 3, 5))

        img_seg = torch.cat([r, g, b], 0)
        img_seg = Image.fromarray(img_seg.permute(1, 2, 0).byte().cpu().numpy()).resize(orig_size)
        buffered = io.BytesIO()
        img_seg.save(buffered, format="JPEG")
        img_seg = 'data:image/jpeg;base64,' + base64.b64encode(buffered.getvalue()).decode("utf-8")
        pred['masks'] = img_seg
    return pred