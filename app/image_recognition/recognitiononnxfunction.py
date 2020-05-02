import json, time, colorsys, random, os
import numpy as np
import boto3
from PIL import Image
import base64
from io import BytesIO
import onnxruntime as ort


# import requests

class NumpyTransforms():
    """
    Performs PIL Image transformation before feeding the data to a model.
    The transformations it perform are:
        - image resize to defined image_size for max(height/width) proportionally
        - convert to numpy array
        - input normalization (mean subtraction and std division)
        - pad numpy array to size
            padded_size*padded_size that are multiplies of size_divisible
    It returns a numpy array and a resized image size without padding
    """

    def __init__(self, image_size=800, size_divisible=32, image_mean=[0.485, 0.456, 0.406],
                 image_std=[0.229, 0.224, 0.225]):
        self.image_size = image_size
        self.mean = np.array(image_mean, dtype=np.float32)
        self.std = np.array(image_std, dtype=np.float32)
        self.size_divisible = size_divisible

    def __call__(self, image, normalize=True):
        if not isinstance(image, Image.Image):
            raise ValueError("image is expected to be PIL Image "
                             ", got {}".format(type(image)))
        image = self.resize(image, self.image_size)
        image = self.from_PIL(image)
        if normalize:
            image = (image - self.mean[:, None, None]) / self.std[:, None, None]
        image_size = image.shape[-2:]
        image = self.batch_image(image, self.size_divisible)[None]
        return image, image_size

    def from_PIL(self, img):
        return np.array(img, dtype=np.float32).transpose(2, 0, 1) / 255

    def to_PIL(self, img):
        # only one image [C, H ,W] is allowed
        if img.ndim > 3: img = img[0]
        return Image.fromarray((img.transpose(1, 2, 0) * 255).astype(np.uint8), mode="RGB")

    def denorm_to_PIL(self, img):
        # only one image [C, H ,W] is allowed
        if img.ndim > 3: img = img[0]
        img = (img * self.std[:, None, None]) + self.mean[:, None, None]
        return self.to_PIL(img)

    def batch_image(self, image, size_divisible=32.):
        self.padded_size = int(np.ceil(float(self.image_size) / size_divisible) * size_divisible)

        padding = [(self.padded_size - s2) for s2 in image.shape[-2:]]
        padded_img = np.pad(image, ((0, 0), (0, padding[0]), (0, padding[1])))
        return padded_img

    def resize(self, image, size):
        w, h = image.size
        scale_factor = size / h
        if w * scale_factor > self.image_size:
            scale_factor = self.image_size / w
        new_h = int(h * scale_factor)
        new_w = int(w * scale_factor)
        return image.resize((new_w, new_h), Image.BILINEAR)


models_dict = {
    "mobilenet_v2800": 'mobilenetv2_onnx_v11_800x800.onnx',
    "resnet34800": 'resnet34_onnx_v11_800x800.onnx',
    "resnet101800": 'resnet101_onnx_v11_800x800.onnx',
    "mobilenet_v2224": 'mobilenetv2_onnx_v11_224x224.onnx',
    "resnet34224": 'resnet34_onnx_v11_224x224.onnx',
    "resnet101224": 'resnet101_onnx_v11_224x224.onnx',
}

def lambda_handler(event, context):
    status = "OK"
    data = None

    if True:  # event['httpMethod'] == 'POST':
        timings = None
        array = event.get('data', None)
        size = event.get("size", None)
        model = event.get("model", None)
        topN =event.get("topN", 5)

        if (array is not None) and \
                (size is not None) and \
                (model is not None):

            start_time = time.time()

            img = Image.open(BytesIO(base64.b64decode(array))).convert('RGB')
            image_orig_size = img.size
            transform = NumpyTransforms(image_size=size)
            inp, img_size = transform(img, normalize=True)
            transform_input_time = round(time.time() - start_time, 2)

            # loading model
            model_key = f'{model}{size}'.lower()
            t = time.time()
            if not os.path.exists(f'/tmp/{models_dict[model_key]}'):
                s3 = boto3.resource('s3')
                s3.Bucket('onnx-models').download_file(models_dict[model_key],
                                                       f'/tmp/{models_dict[model_key]}')
            model_load_time = round(time.time() - t, 2)

            t = time.time()
            ort_session = ort.InferenceSession(f'/tmp/{models_dict[model_key]}')
            session_creation_time = round(time.time() - t, 2)

            t = time.time()
            # onnx model`s out is a list. Taking first element
            # and taking first image because only one image in the batch is considered for now
            out = ort_session.run(None, {'image_input': inp})[0][0]
            model_prediction_time = round(time.time() - t, 2)

            # Softmax
            out = np.exp(out)
            out = out / out.sum()
            # taking topN probabilities
            predicted_idx = np.argsort(out)[-topN:][::-1]
            predicted_scores = out[predicted_idx]

            data = json.dumps({'predicted_idx': predicted_idx.tolist(),
                               'predicted_scores': predicted_scores.tolist(),
                               'img_size': img_size,
                               'image_orig_size': image_orig_size
                               })

            all_time = round(time.time() - start_time, 2)
            timings = {
                "all_time": all_time,
                "transform_input_time": transform_input_time,
                "model_load_time": model_load_time,
                "session_creation_time": session_creation_time,
                "model_prediction_time": model_prediction_time,
            }

        else:
            status = "No input image or size&model parameters!"

    return {
        "status": status,
        "data": data,
        "time": timings
    }