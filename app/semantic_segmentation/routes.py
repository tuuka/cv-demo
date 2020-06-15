from flask import render_template
from app.semantic_segmentation import bp
from flask_babel import _, lazy_gettext as _l
from app.utils import get_mode_img_filename, get_text_from_babel_file


mode = 'semantic_segmentation'
mode_description = {'title': _l('Semantic segmentation'),
                    'desc_html': f'{mode}/modal_description.html'}
models_list = [
   {'name': 'ResNetFCN',
    'active': 'true',
    'id':'resnet101_fcn_coco20',
    'card_header': _l('Pretrained on the COCO Pascal VOC (20 classes) dataset.'),
    'description': f'{mode}/resnetfcn_description.html',
    'dataset': 'pascal',
    'img_size': 600},
   {'name': 'ResNetDeepLab',
    'active': 'false',
    'id':'resnet101_deeplab_coco20',
    'card_header': _l('Pretrained on the COCO Pascal VOC (20 classes) dataset.'),
    'description': f'{mode}/resnetdeeplab_description.html',
    'dataset': 'pascal',
    'img_size': 600},
]

@bp.route('/semantic_segmentation/', methods=['GET', 'POST'])
@bp.route('/semantic_segmentation/index.html', methods=['GET', 'POST'])
def index():
    pascal = get_text_from_babel_file('pascal_class_index.txt')
    labels = {
        'pascal': [_(l) for l in pascal],
    }

    return render_template('topics_index.html',
                           title=_('Semantic segmentation'),
                           mode=mode,
                           mode_img=get_mode_img_filename(mode),
                           models_list=models_list,
                           mode_description=mode_description,
                           labels=labels,
                           topN=10
                           )





