import json
import requests
from flask_babel import _
from flask import current_app as app


def translate(text, source_language, dest_language):
    if 'TRANSLATOR_KEY' not in app.config or \
            not app.config['TRANSLATOR_KEY']:
        return _('Error: the translation service is not configured.')
    auth = app.config['TRANSLATOR_KEY']
    r = requests.get('https://translate.yandex.net/api/v1.5/tr.json/translate?key={}&text={}&lang={}'.format(
        auth, text, dest_language))

    if r.status_code != 200:
        return _('Error: the translation service failed.')
    result = json.loads(r.content.decode('utf-8-sig'))['text'][0]
    return result


def detect_language(text):
    if 'TRANSLATOR_KEY' not in app.config or \
            not app.config['TRANSLATOR_KEY']:
        return _('Error: the translation service is not configured.')
    auth = app.config['TRANSLATOR_KEY']
    r = requests.get('https://translate.yandex.net/api/v1.5/tr.json/detect?key={}&text={}'.format(
        auth, text))
    if r.status_code != 200:
        return _('Error: the translation service failed.')
    return json.loads(r.content.decode('utf-8-sig'))['lang']