from flask import render_template
from app.semantic_segmentation import bp
from flask_babel import _

@bp.route('/semantic_segmentation/', methods=['GET'])
@bp.route('/semantic_segmentation/index.html', methods=['GET'])
def index():
    return render_template('semantic_segmentation/index.html', title=_('Semantic segmentation'))
