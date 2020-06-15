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
    SEND_FILE_MAX_AGE_DEFAULT = 300
    DEBUG = str2bool(os.environ.get('DEBUG', False))
    DETECTION_SCORE_THRESHOLD = float(os.environ.get('DETECTION_SCORE_THRESHOLD', 0.7))
    USE_GPU = str2bool(os.environ.get('USING_GPU', False))
    BOTO3_SERVICES = ['S3', 's3', 'lambda']
    BOTO3_REGION = 'us-west-2'

    # Call lambda function local from python file (not from aws)
    LAMBDA_LOCAL = str2bool(os.environ.get('LAMBDA_LOCAL', False))

    # Call lambda from client JS request (not from /predict route)
    LAMBDA_FROM_JS = str2bool(os.environ.get('LAMBDA_FROM_JS', True))

    # lambda aws url
    LAMBDA_URL = os.environ.get('LAMBDA_URL', None)



