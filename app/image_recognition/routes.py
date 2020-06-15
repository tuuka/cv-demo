from flask import render_template
from app.image_recognition import bp
from flask_babel import _, lazy_gettext as _l
from app.utils import get_mode_img_filename
from app.utils import get_text_from_babel_file


mode = 'image_recognition'
mode_description = {'title': _l('Image recognition'),
                    'desc_html': f'{mode}/modal_description.html'}

models_list = [
   {'name': 'MobileNetV2',
    'active': 'true',
    'id':'mobilenetv2',
    'card_header': _l('Pretrained on the ImageNet1000 dataset.'),
    'description': f'{mode}/mobilenetv2_description.html',
    'dataset': 'imagenet',
    'img_size': 224},
   {'name': 'ResNet34',
    'active': 'false',
    'id':'resnet34',
    'card_header': _l('Pretrained on the ImageNet1000 dataset.'),
    'description': f'{mode}/resnet_description.html',
    'dataset': 'imagenet',
    'img_size': 224},
   {'name': 'Resnet101',
    'active': 'false',
    'id':'resnet101',
    'card_header': _l('Pretrained on the ImageNet1000 dataset.'),
    'description': f'{mode}/resnet_description.html',
    'dataset': 'imagenet',
    'img_size': 224},
]


@bp.route('/image_recognition/', methods=['GET', 'POST'])
@bp.route('/image_recognition/index.html', methods=['GET', 'POST'])
def index():
    imagenet = get_text_from_babel_file('imagenet_class_index.txt')
    labels = {
        'imagenet': [_(l) for l in imagenet],
    }
    return render_template('topics_index.html',
                           title=_('Image recognition'),
                           mode=mode,
                           mode_img=get_mode_img_filename(mode),
                           models_list=models_list,
                           mode_description=mode_description,
                           labels=labels,
                           topN=5
                           )

