from backend.extensions import db
from flask import jsonify, Blueprint
from backend.models import Category # 导入数据库模型
from backend.utils.response import success_response


category_bp = Blueprint('category', __name__, url_prefix='/api')
# # 模拟分类数据，这些都是写死的数据，假数据
# category_list = [
#     {"id":1, "name": "手机"},
#     {"id":2, "name": "电脑"},
#     {"id":3, "name": "家电"}
# ]

@category_bp.route('/category', methods=['GET'])
def get_category():
    # 从数据库查询所有分类
    categories = Category.query.all()
    # 把数据库对象转成JSON需要的字典格式
    result = []
    for cate in categories:
        result.append({
            "id": cate.id,
            "name": cate.name
        })

    return success_response(data=result)