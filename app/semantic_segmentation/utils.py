import torch, io, base64
from PIL import Image
from app.semantic_segmentation import models
from app.utils import transform_image, hex_colors, random_colors


labels_pascal = ['background', 'aeroplane', 'bicycle', 'bird', 'boat', 'bottle', 'bus',
          'car', 'cat', 'chair', 'cow', 'dining table', 'dog', 'horse', 'motorbike',
          'person', 'potted plant', 'sheep', 'sofa', 'train', 'tv/monitor']


class_colors_pascal = torch.tensor([
    (0, 0, 0),  # 0 - background
    (128, 0, 0),  # 1 - aeroplane
    (0, 128, 0),  # 2 - bicycle
    (128, 128, 0),  # 3 - bird
    (0, 0, 128),  # 4 - boat
    (128, 0, 128),  # 5 - bottle
    (0, 128, 128),  # 6 - bus
    (128, 128, 128),  # 7 - car
    (64, 0, 0),  # 8 - cat
    (192, 0, 0),  # 9 - chair
    (64, 128, 0),  # 10 - cow
    (192, 128, 0),  # 11 - dining table
    (64, 0, 128),  # 12 - dog
    (192, 0, 128),  # 13 - horse
    (64, 128, 128),  # 14 - motorbike
    (192, 128, 128),  # 15 - person
    (0, 64, 0),  # 16 - potted plant
    (128, 64, 0),  # 17 - sheep
    (0, 192, 0),  # 18 - sofa
    (128, 192, 0),  # 19 - train
    (0, 64, 128),  # 20 - tv/monitor
]).byte()


def color_mapping(img, class_colors):
    r = torch.zeros_like(img).byte()
    g = torch.zeros_like(img).byte()
    b = torch.zeros_like(img).byte()
    for i, color in enumerate(class_colors):
        mask = img == i
        r[mask] = color[0]
        g[mask] = color[1]
        b[mask] = color[2]
    return torch.cat([r.unsqueeze(0), g.unsqueeze(0), b.unsqueeze(0)], 0)


def get_prediction(modelname=None, image_bytes=None):
    if (image_bytes is None) or (modelname is None): return None
    img, orig_size = transform_image(image_bytes, resize_to_size=320)
    model = models.model_load(modelname)
    model.eval()
    with torch.no_grad():
        out = model(img)['out'].squeeze()
        img_seg = torch.argmax(out, 0)
        classes_in_image, counts = torch.unique(img_seg, return_counts=True)
        # take top10 classes only
        classes_in_image = classes_in_image[torch.argsort(counts, descending=True)].tolist()[:10]
        classes_in_image = [(labels_pascal[i], hex_colors(class_colors_pascal[i])) for i in classes_in_image]
        img_seg = color_mapping(img_seg, class_colors_pascal)
    img_seg = Image.fromarray(img_seg.permute(1, 2, 0).byte().numpy()).resize(orig_size)
    buffered = io.BytesIO()
    img_seg.save(buffered, format="JPEG")
    img_seg = 'data:image/jpeg;base64,' + base64.b64encode(buffered.getvalue()).decode("utf-8")
    return img_seg, classes_in_image
