import os

def str2bool(s):
    try:
        if s.lower() in ('yes', 'true', '1', 'y'):
            return True
        else:
            return False
    except:
        return s


class Config(object):
    SECRET_KEY = os.environ.get('SECRET_KEY', 'you-will-never-guess')
    PORT = 5000
    LANGUAGES = ['ru', 'en']
    TRANSLATOR_KEY = os.environ.get('YANDEX_TRANSLATOR_KEY')
    DEBUG = str2bool(os.environ.get('DEBUG', False))
    DETECTION_SCORE_THRESHOLD = float(os.environ.get('DETECTION_SCORE_THRESHOLD', 0.7))
    USE_GPU = str2bool(os.environ.get('USING_GPU', False))
    BOTO3_SERVICES = ['S3', 's3', 'lambda']
    BOTO3_REGION = 'us-west-2'
    ONNX_IMAGE_SIZE = int(os.environ.get('ONNX_IMAGE_SIZE', 800))
    LAMBDA_LOCAL = str2bool(os.environ.get('LAMBDA_LOCAL', False))
    LAMBDA_URL = os.environ.get('LAMBDA_URL', None)
    CACHE_TYPE = 'filesystem'
    CACHE_DEFAULT_TIMEOUT = int(os.environ.get('CACHE_DEFAULT_TIMEOUT', 300))
    CACHE_DIR = '/tmp/'
    CACHE_THRESHOLD = int(os.environ.get('CACHE_THRESHOLD', 20))
