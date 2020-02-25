from torchvision import models
from app.utils import load_model

models_dict = {
    'maskrcnn_resnet50_fpn_coco'  : models.detection.maskrcnn_resnet50_fpn,
}

model_urls = {
    'maskrcnn_resnet50_fpn_coco':
        'https://download.pytorch.org/models/maskrcnn_resnet50_fpn_coco-bf2d0c1e.pth',
}


def model_load(name='maskrcnn_resnet50_fpn_coco'):
    model = models_dict.get(name, models.detection.maskrcnn_resnet50_fpn)(pretrained=False, pretrained_backbone=False)
    model = load_model(model, model_urls[name])
    return model
