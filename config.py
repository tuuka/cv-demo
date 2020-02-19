import os

class Config(object):
    LANGUAGES = ['ru', 'en']
    TRANSLATOR_KEY = os.environ.get('YANDEX_TRANSLATOR_KEY')
    DETECTION_SCORE_THRESHOLD = os.environ.get('DETECTION_SCORE_THRESHOLD', 0.7)
    USE_GPU = os.environ.get('USING_GPU', False)

