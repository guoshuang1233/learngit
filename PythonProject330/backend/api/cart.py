from flask import Blueprint, request, json
from backend.extensions import db
from backend.models import Cart, Goods
from backend.utils.redis_client import redis_client
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

    # cart = Cart.query.filter_by(user_id=user_id, goods_id=goods_id).first()
    # 找到这个用户的购物车
    cart_key = f"cart:{user_id}"
    # 看看购物车里有没有这个商品
    existing = redis_client.hget(cart_key, goods_id)

    if existing:
        cart_data = json.loads(existing) # 取数据，把字符串转成字典,好进行数量修改
        cart_data["count"] += count # 存在则数量叠加
        redis_client.hset(cart_key, goods_id, json.dumps(cart_data)) # 存回购物车，redis不能存字典，需转成字符串
    else: # 新增,构造你想存的商品信息
        cart_data = {
            "goods_id": goods_id,
            "count": count, # 购物车核心
            "is_selected": True, # 是否勾选，结算时要用
            "create_time": None
        }
        # 直接加入购物车，# hset的固定格式： redis_client.hset(大key, 小field, value)
        # cart_key(哪个用户的购物车)，good_id(哪个商品)，json.dumps(cart_data)-商品信息字符串
        redis_client.hset(cart_key, goods_id, json.dumps(cart_data))

    return success_response(msg="加入购物车成功")

@cart_bp.route("/list", methods=["GET"])
@jwt_required
def cart_list():
    user_id = request.current_user_id
    # cart_list = Cart.query.filter_by(user_id=user_id).order_by(Cart.create_time.desc()).all()
    cart_key = f"cart:{user_id}"
    cart_hash = redis_client.hgetall(cart_key) # 返回字典 {goods_id: json字符串}，cart_json就是字典的value

    result = []
    # 遍历Redis中取出的购物车数据
    for goods_id, cart_json in cart_hash.items():
        cart_data = json.loads(cart_json)
        goods = Goods.query.get(goods_id)
        if goods:
            result.append({
                "id": goods.id,
                "goods_id": int(goods_id),
                "goods_name": goods.name,
                "goods_image": goods.img,
                "price": float(goods.price),
                "count": cart_data["count"],
                "is_selected": cart_data.get("is_selected", True),
                "create_time":cart_data.get("create_time")
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

    cart_key = f"cart:{user_id}"
    existing = redis_client.hget(cart_key, cart_id)
    if not existing:
        raise ApiException("购物车记录不存在", 404)

    cart_data = json.loads(existing)
    cart_data["count"] = count
    redis_client.hset(cart_key, cart_id, json.dumps(cart_data))

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

    cart_key = f"cart:{user_id}"
    deleted = redis_client.hdel(cart_key, cart_id)
    if not deleted:
        raise ApiException("记录不存在", 404)
    return success_response(msg="删除成功")

@cart_bp.route("/clear", methods=["POST"])
@jwt_required
def clear_cart():
    user_id = request.current_user_id
    cart_key = f"cart:{user_id}"
    redis_client.delete(cart_key)
    return success_response(msg="清空购物车成功")

@cart_bp.route("/merge", methods=["POST"])
@jwt_required
def merge_cart():
    """
    登录后合并前端localStorage购物车到后端数据库
    前端传参： cart_list = 【{goods_id: 1,count: 2}, ...】
    """
    user_id = request.current_user_id
    data = request.get_json()
    local_cart_list = data.get("cart_list", []) # 加空列表，防止代码崩溃

    # 无本地购物车直接返回
    if not local_cart_list:
        return success_response(msg="无本地购物车,合并完成")

    # 遍历本地购物车，逐条合并到数据库
    for item in local_cart_list:
        goods_id = item.get("goods_id")
        count = int(item.get("count", 1))

        # 过滤无效数据
        if not goods_id or count < 1:
            continue
        # 检验商品是否存在
        goods = Goods.query.get(goods_id)
        if not goods:
            continue
        # 查询用户购物车是否已有该商品
        cart = Cart.query.filter_by(user_id=user_id, goods_id=goods_id).first()
        if cart:
            # 已有则累加
            cart.count += count
        else:
            # 无商品：新增
            new_cart = Cart(user_id=user_id, goods_id=goods_id, count=count)
            db.session.add(new_cart)
    db.session.commit()
    return success_response(msg="本地购物车合并成功")
