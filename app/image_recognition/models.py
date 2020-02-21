from torchvision import models
import torch, os, sys, requests
from urllib.request import urlretrieve
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