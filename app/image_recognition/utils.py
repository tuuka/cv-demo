from PIL import Image
import torch, json, io
import torchvision.transforms as transforms
from app.image_recognition import models

with open('app/static/imagenet_class_index.json') as json_file:
    imagenet_class = json.load(json_file)

def get_prediction(modelname=None, image_bytes=None, n=5):
    if (image_bytes is None) or (modelname is None): return None
    img = transform_image(image_bytes, resize_to_size=224)
    model = models.model_load(modelname)
    model.eval()
    with torch.no_grad():
        outputs = model(img).squeeze()
        outputs = torch.nn.functional.softmax(outputs, dim=-1)
    predicted_idx = torch.argsort(outputs, descending=True)[:n].tolist()
    pred = [[str(round(100*outputs[p].item()))]+[imagenet_class[str(p)][0]] + \
          [imagenet_class[str(p)][1].replace('_', ' ')] for p in predicted_idx]
    return pred

def transform_image(image_bytes, mean = [0.485, 0.456, 0.406], std = [0.229, 0.224, 0.225], resize_to_size=None):
    t = [transforms.ToTensor()]
    if resize_to_size is not None:
        t.insert(0, transforms.Resize(resize_to_size))
    if (mean is not None) & (std is not None):
        t.append(transforms.Normalize(mean, std))
    my_transforms = transforms.Compose(t)
    image = Image.open(io.BytesIO(image_bytes)).convert('RGB')
    return my_transforms(image).unsqueeze(0)