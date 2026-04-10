from flask import Blueprint, request
from backend.extensions import db
from backend.models import Cart, Goods
from backend.utils.response import success_response
from backend.utils.exceptions import ApiException
from backend.utils.jwt_auth import jwt_required

cart_bp = Blueprint("cart", __name__, url_prefix="/api/cart")

@cart_bp.route("/add", methods=["POST"])
@jwt_required
def add_cart():
    user_id = request.current_user_id
    data = request.get_json()
    goods_id = data.get("goods_id")
    count = int(data.get("count", 1))

    if not goods_id:
        raise ApiException("商品ID不能为空", 400)
    if count < 1:
        raise ApiException("商品数量不能小于1", 400)

    goods = Goods.query.get(goods_id)
    if not goods:
        raise ApiException("商品不存在", 404)

    cart = Cart.query.filter_by(user_id=user_id, goods_id=goods_id).first()

    if cart:
        cart.count += count
    else:
        cart = Cart(
            user_id=user_id,
            goods_id=goods_id,
            count=count
        )
        db.session.add(cart)

    db.session.commit()
    return success_response(msg="加入购物车成功")

@cart_bp.route("/list", methods=["GET"])
@jwt_required
def cart_list():
    user_id = request.current_user_id
    cart_list = Cart.query.filter_by(user_id=user_id).order_by(Cart.create_time.desc()).all()

    result = []
    for cart in cart_list:
        result.append({
            "id": cart.id,
            "goods_id": cart.goods_id,
            "goods_name": cart.goods.name,
            "goods_image": cart.goods.img,
            "count": cart.count,
            "is_selected": cart.is_selected,
            "create_time": cart.create_time.strftime("%Y-%m-%d %H:%M:%S") if cart.create_time else None
        })
    return success_response(data=result)

@cart_bp.route("/update", methods=["POST"])
@jwt_required
def update_cart():
    user_id = request.current_user_id
    data = request.get_json()
    cart_id = data.get("cart_id")
    count = int(data.get("count", 1))

    if not cart_id or count < 1:
        raise ApiException("参数错误：购物车ID不能为空，数量≥1", 400)

    cart = Cart.query.filter_by(id=cart_id, user_id=user_id).first()
    if not cart:
        raise ApiException("购物车记录不存在", 404)

    cart.count = count
    db.session.commit()

    return success_response(msg="修改成功")

@cart_bp.route("/delete", methods=["POST"])
@jwt_required
def delete_cart():
    user_id = request.current_user_id
    data = request.get_json()
    cart_id = data.get("cart_id")

    if not cart_id:
        raise ApiException("购物车ID不能为空", 400)

    cart = Cart.query.filter_by(id=cart_id, user_id=user_id).first()
    if not cart:
        raise ApiException("记录不存在", 404)

    db.session.delete(cart)
    db.session.commit()
    return success_response(msg="删除成功")

@cart_bp.route("/clear", methods=["POST"])
@jwt_required
def clear_cart():
    user_id = request.current_user_id
    Cart.query.filter_by(user_id=user_id).delete()
    db.session.commit()
    return success_response(msg="清空购物车成功")
