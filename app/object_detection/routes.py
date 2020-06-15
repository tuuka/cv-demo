from flask import render_template
from app.object_detection import bp
from flask_babel import _, lazy_gettext as _l
from app.utils import get_mode_img_filename, get_text_from_babel_file

mode = 'object_detection'
mode_description = {'title': _l('Object detection'),
                    'desc_html': f'{mode}/modal_description.html'}
models_list = [
   {'name': 'MaskRCNN',
    'active': 'true',
    'id':'maskrcnn_resnet50_fpn_coco',
    'card_header': _l('Pretrained on the COCO 2017 (91 class) dataset. Perform instance segmentation task as well.'),
    'description': f'{mode}/maskrcnn_description.html',
    'dataset': 'coco2017',
    'img_size': 800,
    'threshold': 0.70},
   # {'name': 'MaskRCNN(quant)',
   #  'active': 'false',
   #  'id': 'maskrcnn_quantized',
   #  'card_header': _l('Pretrained on the COCO 2017 (91 class) dataset. Perform instance segmentation task as well.'),
   #  'description': f'{mode}/maskrcnn_description.html',
   #  'dataset': 'coco2017',
   #  'img_size': 800,
   #  'threshold': 0.70},
]

@bp.route('/object_detection/', methods=['GET', 'POST'])
@bp.route('/object_detection/index.html', methods=['GET', 'POST'])
def index():
    coco2017 = get_text_from_babel_file('coco2017_class_index.txt')
    labels = {
        'coco2017': [_(l) for l in coco2017],
    }
    return render_template('topics_index.html',
                           title=_('Object detection'),
                           mode=mode,
                           mode_img=get_mode_img_filename(mode),
                           models_list=models_list,
                           mode_description=mode_description,
                           labels=labels,
                           topN=10
                           )

