from torchvision import models
from app.utils import load_model
models_dict = {
    'resnet101': models.resnet101,
    'resnet34': models.resnet34,
    'mobilenet_v2': models.mobilenet_v2
}
model_urls = {
    'mobilenet_v2': 'https://download.pytorch.org/models/mobilenet_v2-b0353104.pth',
    'resnet34': 'https://download.pytorch.org/models/resnet34-333f7ec4.pth',
    'resnet101': 'https://download.pytorch.org/models/resnet101-5d3b4d8f.pth',
}
def model_load(name='mobilenet_v2'):
    model = models_dict.get(name, models.mobilenet_v2)(pretrained=False)
    model = load_model(model, model_urls[name])
    return model

