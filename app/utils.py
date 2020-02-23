import torch, io, os, sys, random, requests, colorsys
import torchvision.transforms as transforms
from urllib.request import urlretrieve
from PIL import Image



def load_model(model, url, model_dir='/tmp/pretrained', map_location=torch.device('cpu')):
    # Предполагаем, что ссылки на google drive не содержат символа "/", в отличие от url-ссылок
    google_drive = False if '/' in url else True
    if not os.path.exists(model_dir): os.makedirs(model_dir)
    filename = url.split('/')[-1]
    if google_drive: filename = url + '.pth'
    cached_file = os.path.join(model_dir, filename)
    # Если файл скачан ранее, загружаем веса из него
    if os.path.exists(cached_file):
        checkpoint = torch.load(cached_file, map_location=map_location)
    else:
        if not google_drive: # скачиваем файл по url-ссылке
            sys.stderr.write('Downloading: "{}" to {}\n'.format(url, cached_file))
            urlretrieve(url, cached_file)
        else:                # скачиваем из google drive
            sys.stderr.write('Downloading: "{}" to {}\n'.format('model weights from google drive', cached_file))
            download_file_from_google_drive(url, cached_file)
        checkpoint = torch.load(cached_file, map_location=map_location)
    # Если в checkpoint сохранена не только модель:
    if 'model' in checkpoint.keys(): checkpoint = checkpoint['model']
    model.load_state_dict(checkpoint)
    return model

def download_file_from_google_drive(id, destination):
    def get_confirm_token(resp):
        for key, value in resp.cookies.items():
            if key.startswith('download_warning'):
                return value
        return None
    def save_response_content(resp, dest):
        CHUNK_SIZE = 32768
        with open(dest, "wb") as f:
            for chunk in resp.iter_content(CHUNK_SIZE):
                if chunk:  # filter out keep-alive new chunks
                    f.write(chunk)
    URL = "https://docs.google.com/uc?export=download"
    session = requests.Session()
    response = session.get(URL, params={'id': id}, stream=True)
    token = get_confirm_token(response)
    if token:
        params = {'id': id, 'confirm': token}
        response = session.get(URL, params=params, stream=True)
    save_response_content(response, destination)

def transform_image(image_bytes, mean = [0.485, 0.456, 0.406], std = [0.229, 0.224, 0.225], resize_to_size=None):
    t = [transforms.ToTensor()]
    if resize_to_size is not None:
        t.insert(0, transforms.Resize(resize_to_size))
    if (mean is not None) & (std is not None):
        t.append(transforms.Normalize(mean, std))
    my_transforms = transforms.Compose(t)
    image = Image.open(io.BytesIO(image_bytes)).convert('RGB')
    return my_transforms(image).unsqueeze(0), image.size


def hex_colors(col):
    def clamp(x):
        return max(0, min(x, 255))
    return "#{0:02x}{1:02x}{2:02x}".format(clamp(col[0]), clamp(col[1]), clamp(col[2]))

def random_colors(N, bright=True):
    """
    Generate random colors.
    To get visually distinct colors, generate them in HSV space then
    convert to RGB.
    """
    brightness = 1.0 if bright else 0.7
    hsv = [(i / N, 1, brightness) for i in range(N)]
    colors = list(map(lambda c: colorsys.hsv_to_rgb(*c), hsv))
    random.shuffle(colors)
    return [hex_colors((round(r*255), round(g*255), round(b*255)))
            for r,g,b in colors]


