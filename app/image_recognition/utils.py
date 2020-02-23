import torch, json
from app.image_recognition import models
from app. utils import transform_image

with open('app/static/imagenet_class_index.json') as json_file:
    imagenet_class = json.load(json_file)

def get_prediction(modelname=None, image_bytes=None, n=5):
    if (image_bytes is None) or (modelname is None): return None
    img, _ = transform_image(image_bytes, resize_to_size=224)
    model = models.model_load(modelname)
    model.eval()
    with torch.no_grad():
        outputs = model(img).squeeze()
        outputs = torch.nn.functional.softmax(outputs, dim=-1)
    predicted_idx = torch.argsort(outputs, descending=True)[:n].tolist()
    pred = [[str(round(100*outputs[p].item()))]+[imagenet_class[str(p)][0]] + \
          [imagenet_class[str(p)][1].replace('_', ' ')] for p in predicted_idx]
    return pred

