from torchvision import models
from app.utils import load_model

models_dict = {
    'resnet101_deeplab_coco20' : models.segmentation.deeplabv3_resnet101,
    'resnet101_fcn_coco20' : models.segmentation.fcn_resnet101,
}

model_urls = {
    'resnet101_fcn_coco20':              'https://download.pytorch.org/models/fcn_resnet101_coco-7ecb50ca.pth',
    'resnet101_deeplab_coco20':          'https://download.pytorch.org/models/deeplabv3_resnet101_coco-586e9e4e.pth',
}

def model_load(name='resnet101_fcn_coco20'):
    model = models_dict.get(name, models.segmentation.fcn_resnet101)(pretrained=False, aux_loss=True, pretrained_backbone=False)
    model = load_model(model, model_urls[name])
    return model