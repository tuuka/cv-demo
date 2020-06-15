import json

import requests
from flask import render_template, request, g, jsonify, current_app as app
from flask import make_response, send_from_directory
from flask_babel import _, get_locale, lazy_gettext as _l

from app.main import bp
from app.utils import get_text_from_babel_file

work_modes = ["image_recognition", "semantic_segmentation", "object_detection"]
powered_by_list = [
    {'icon': 'icons/python.png',
     'href': 'https://www.python.org/',
     'name': 'Python'},
    {'icon': 'icons/flask.png',
     'href': 'https://flask.palletsprojects.com/',
     'name': 'Flask'},
    {'icon': 'icons/pytorch.svg',
     'href': 'https://pytorch.org/',
     'name': 'PyTorch'},
    {'icon': 'icons/bootstrap.svg',
     'href': 'https://getbootstrap.com/',
     'name': 'Bootstrap'},
    {'icon': 'icons/pycharm.svg',
     'href': 'https://www.jetbrains.com/pycharm/',
     'name': 'PyCharm'},
    {'icon': 'icons/colab.png',
     'href': 'https://colab.research.google.com/',
     'name': 'Google Colab'},
    {'icon': 'icons/heroku.svg',
     'href': 'https://www.heroku.com/',
     'name': 'Heroku'},
    {'icon': 'icons/google_cloud.svg',
     'href': 'https://cloud.google.com/',
     'name': 'Google Cloud'},
    {'icon': 'icons/aws.svg',
     'href': 'https://aws.amazon.com/',
     'name': 'Amazon Web Service'},
]

inspired_list = [
    {'icon': 'icons/stanford.svg',
     'href': 'http://cs231n.stanford.edu/',
     'name': 'Stanford CS231N'},
    {'icon': 'icons/ods.svg',
     'href': 'https://ods.ai/',
     'name': 'OpenDataScience'},
]

topics = [
    {'name': _l('Image recognition'),
     'id': 'image_recognition',
     'image': 'images/c-1.jpg',
     'tooltip': _l(
         'Labeling of the most significant\nobject (objects) in the image from\na predetermined class list.')},
    {'name': _l('Semantic segmentation'),
     'id': 'semantic_segmentation',
     'image': 'images/c-2.jpg',
     'tooltip': _l(
         'Dividing the image into separate groups, areas\nof pixels belonging to one particular class of\nobjects while marking these areas with color.')},
    {'name': _l('Object detection'),
     'id': 'object_detection',
     'image': 'images/c-3.jpg',
     'tooltip': _l('Location and labeling of objects in\nthe image independent for each instance\nof the object.')},
]

about_topics = [
    {
        'title': 'Идея.',
        'id': '0',
        'short': '''Самое тяжелое всегда - определиться с чего начать. Размышления, типа "получится/не получится, 
        хватит времени или нет, надо ли оно вообще" заводят в тупик. Требуются некоторые усилия, чтобы отбросить их, 
        направив мысли в нужное русло...''',
    },
    {
        'title': 'Каркас.',
        'id': '1',
        'short': '''Итак, из пройденых курсов я знаю принципы работы искусственных нейронных сетей, их основные типы и 
        решаемые задачи. Так как область компьютерного зрения, все-таки, немного попроще NLP, я решил пока рассматривать 
        именно ее.''',
    },
    {
        'title': 'Основной функционал.',
        'id': '2',
        'short': '''Имплементация готовых предобученных моделей. Html-шаблоны, маршруты, JS-запросы и ответы Flask-API. 
        Отображение результатов.''',
    },
    {
        'title': 'Google Colab',
        'id': '3',
        'short': '''Не стандартное использование Google Colab для <strike>нищебродов</strike> нуждающихся в нормальном 
        "железе" при разработке достаточно сложных модульных (в том числе и веб) приложений.''',
    },
    {
        'title': 'Развертывание. Попытка первая.',
        'id': '4',
        'short': '''Выбор хостинга, достоинства и недостатки. Что бесплатно всегда, что не всегда, что никогда. Как 
        удобнее и быстрее всего разместить свое приложение новичку в интернете.''',
    },
    {
        'title': 'Quantization. Scripting.',
        'id': '5',
        'short': '''Нужна ли float32 точность на самом деле? Как сохранить PyTorch модель целиком, а не 
        только ее веса?''',
    },
    {
        'title': 'Развертывание. Попытка вторая.',
        'id': '6',
        'short': '''Бессерверные приложения Amazon, Lambda - функции. Компромисс производительности и стоимости.''',
    },
    {
        'title': 'Лучшее - враг хорошего.',
        'id': '7',
        'short': '''Рефакторинг. Вызов Lambda из клиентского Javascript, кеширование, прочие улучшения и оптимизация.''',
    },
]


@bp.before_app_request
def before_request():
    g.locale = str(get_locale())
    g.work_modes = work_modes
    g.inspired = inspired_list
    g.powered = powered_by_list
    g.topics = topics
    g.lambda_url = app.config.get('LAMBDA_URL') if app.config.get('LAMBDA_FROM_JS') else "/predict"


@bp.route('/', methods=['GET', 'POST'])
@bp.route('/index', methods=['GET', 'POST'])
def index():
    main_index_description = [_(x) for x in get_text_from_babel_file('main_index_description.txt')]
    return render_template('index.html',
                           title=_('Home'),
                           mode='main_page',
                           main_index_description=main_index_description)


@bp.route('/about', methods=['GET'])
def about():
    return render_template('about/about.html',
                           title=_('About'),
                           mode='about_page',
                           about_topics=about_topics)


@bp.route('/predict', methods=['POST'])
def predict():
    if request.method == 'POST':
        data = json.loads(request.data)
        try:
            lambda_params = {'size': data['size'],
                             'model': data['model'],
                             'data': data['data'],
                             'topN': data['topN'],
                             'threshold': data['threshold'],
                             'labels': data['labels']
                             }
        except Exception as e:
            app.logger.error(f'Error in data extraction in Flask: {e}.')
            return jsonify({'error': f'Error in data extraction in Flask: {e}.'})

        if app.config.get('LAMBDA_LOCAL'):
            from app.cvdemolambda import lambda_handler
            r = lambda_handler(lambda_params, None)
        else:
            # invokation via boto3 extension (AWS Credential and other params needed)
            '''
            r = invoke_lambda_function_synchronous('nonnxfunction',
                                               lambda_params,
                                               region_name=app.config.get('BOTO3_REGION'))
            r = json.load(r['Payload'])
            '''

            # dont check config value correctness cause try-except in route
            r = requests.post(app.config.get('LAMBDA_URL'),
                              data=json.dumps(lambda_params).encode())
            r = json.loads(r.text)

        return jsonify(r)

# Service worker
@bp.route('/sw.js')
def sw():
    response = make_response(
        send_from_directory('static/js', filename='sw.js'))
    # change the content header file
    response.headers['Content-Type'] = 'application/javascript'
    return response
