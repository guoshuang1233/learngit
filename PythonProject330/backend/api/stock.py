from flask import Blueprint, request
from backend.extensions import db
from backend.models import Goods, User, Category
from backend.utils.response import success_response
from backend.utils.exceptions import ApiException
from backend.utils.jwt_auth import jwt_required

stock_bp = Blueprint('stock', __name__, url_prefix="/api/stock")

@stock_bp.route('/list', methods=["GET"])
@jwt_required
def get_stock_list():
    """获取商品库存列表（仅管理员）"""
    user_id = request.current_user_id
    user = User.query.get(user_id)
    if not user or user.role !=1:
        raise ApiException("无权限", 403)

    page = int(request.args.get('page', 1))
    size = int(request.args.get('size', 20))
    keyword = request.args.get('keyword', '')
    # 查询全部商品（select * from goods）
    query = Goods.query
    if keyword:
        query = query.filter(Goods.name.like(f'%{keyword}%'))
    total = query.count()
    page_data = query.order_by(Goods.id.asc()).paginate(page=page, per_page=size, error_out=False)

    res_list= [{
        "id": g.id,
        "name": g.name,
        "stock": g.stock if g.stock is not None else 0,
        "category_name": Category.query.get(g.cid).name if g.cid and Category.query.get(g.cid) else "",
        "price": g.price
    } for g in page_data.items]

    return success_response(data={
        "total": total,
        "list": res_list
    })


@stock_bp.route('/update', methods=["POST"])
@jwt_required
def update_stock():
    """更新商品库存（仅管理员）"""
    user_id = request.current_user_id
    user = User.query.get(user_id)
    if not user or user.role != 1:
        raise ApiException("无权限", 403)

    data = request.get_json()
    goods = Goods.query.get(data.get("goods_id"))
    if not goods:
        raise ApiException("商品不存在", 404)
    if goods.stock is None or goods.stock < 0:
        raise ApiException("商品库存不能小于0", 400)

    goods.stock = data.get("stock")
    db.session.commit()

    return success_response(msg="更新成功", data={"goods_id": goods.id, "stock": goods.stock})



