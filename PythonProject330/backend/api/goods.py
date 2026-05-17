from flask import request, Blueprint
from backend.service.goods_service import GoodsService
from backend.utils.response import success_response

goods_bp = Blueprint('goods', __name__, url_prefix='/api')
goods_service = GoodsService()

@goods_bp.route('/goods', methods=['GET'])
def get_goods():
    page = int(request.args.get('page', 1))
    size = int(request.args.get('size', 6))
    cid = int(request.args.get('cid', 0))
    name = request.args.get('name', '')

    page_data = goods_service.get_goods_list(page, size, cid, name)

    res_list = [{
        "id": g.id, "name": g.name, "price": g.price, "img": g.img,
        "cid": g.cid, "available": g.stock > 0
    } for g in page_data.items]

    return success_response(data={"total": page_data.total, "list": res_list})
