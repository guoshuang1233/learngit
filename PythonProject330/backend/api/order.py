from flask import Blueprint, request
from backend.extensions import db
from backend.models import Order, OrderItem, Cart, Goods
from backend.utils.response import success_response
from backend.utils.exceptions import ApiException
from backend.utils.jwt_auth import jwt_required
from datetime import datetime
import uuid

order_bp = Blueprint("order", __name__, url_prefix="/api/order")


@order_bp.route("/create", methods=["POST"])
@jwt_required
def create_order():
    """创建订单（虚拟卡支付）- 使用原子操作防止超卖"""
    user_id = request.current_user_id
    cart_items = Cart.query.filter_by(user_id=user_id, is_selected=True).all()

    if not cart_items:
        raise ApiException("购物车为空", 400)

    total_amount = 0
    order_items_data = []

    for cart in cart_items:
        goods = cart.goods
        if not goods:
            raise ApiException("商品不存在", 404)

        stock = goods.stock if hasattr(goods, 'stock') else 0
        if stock < cart.count:
            raise ApiException(f"商品【{goods.name}】库存不足，当前库存：{stock}", 400)

        subtotal = float(goods.price) * cart.count
        total_amount += subtotal
        order_items_data.append({
            "goods_id": goods.id,
            "goods_name": goods.name,
            "goods_price": float(goods.price),
            "count": cart.count,
            "total_price": subtotal
        })

    order_id = datetime.now().strftime("%Y%m%d%H%M%S") + str(uuid.uuid4().hex[:6])

    try:
        order = Order(
            id=order_id,
            user_id=user_id,
            total_amount=total_amount,
            status=1,
            create_time=datetime.now(),
            pay_time=datetime.now()
        )
        db.session.add(order)

        # sorted(列表， key=排序规则， reverse=False) 默认是升序，降序为reverse=True
        for item_data in sorted(order_items_data, key=lambda x: x["goods_id"]):  # lambda x: x["goods_id"]提取规则（按ID排序）
            order_item = OrderItem(
                order_id=order_id,
                goods_id=item_data["goods_id"],
                goods_name=item_data["goods_name"],
                goods_price=item_data["goods_price"],
                count=item_data["count"],
                total_price=item_data["total_price"]
            )
            db.session.add(order_item)

            result = db.session.execute(
                db.text("UPDATE goods SET stock = stock - :count WHERE id = :goods_id AND stock >= :count"),
                {"count": item_data["count"], "goods_id": item_data["goods_id"]}
            )

            if result.rowcount == 0:
                raise ApiException(f"商品【{item_data['goods_name']}】库存不足，下单失败", 400)

        for cart in cart_items:
            db.session.delete(cart)

        db.session.commit()
        return success_response(msg="下单成功", data={
            "order_id": order_id,
            "total_amount": total_amount,
            "status": "已付款"
        })
    except ApiException:
        db.session.rollback()
        raise
    except Exception as e:
        db.session.rollback()
        raise ApiException(f"下单失败：{str(e)}", 500)


@order_bp.route("/cancel/<order_id>", methods=["POST"])
@jwt_required
def cancel_order(order_id):
    """取消订单并恢复库存"""
    user_id = request.current_user_id

    order = Order.query.filter_by(id=order_id, user_id=user_id).first()
    if not order:
        raise ApiException("订单不存在", 404)
    if order.status == 4:
        raise ApiException("订单已取消", 400)

    if order.status != 1:
        raise ApiException("只能取消已付款的订单", 400)

    try:
        items = OrderItem.query.filter_by(order_id=order_id).all()
        for item in items:
            db.session.execute(
                db.text("UPDATE goods SET stock = stock + :count WHERE id = :goods_id"),
                {"count": item.count, "goods_id": item.goods_id}
            )

        order.status = 4
        order.cancel_time = datetime.now()

        db.session.commit()
        return success_response(msg="订单已取消，库存已恢复")
    except Exception as e:
        db.session.rollback()
        raise ApiException("取消订单失败", 500)


@order_bp.route("/list", methods=["GET"])
@jwt_required
def order_list():
    """获取订单列表"""
    user_id = request.current_user_id

    orders = Order.query.filter_by(user_id=user_id).order_by(Order.create_time.desc()).all()

    status_map = {
        0: "待付款",
        1: "已付款",
        2: "已发货",
        3: "已完成",
        4: "已取消"
    }

    result = []
    for order in orders:
        result.append({
            "order_id": order.id,
            "total_amount": float(order.total_mount),
            "status": status_map.get(order.status, "未知状态"),
            "create_time": order.create_time.strftime("%Y-%m-%d %H:%M:%S") if order.create_time else None,
        })

    return success_response(data=result)


@order_bp.route("/detail/<order_id>", methods=["GET"])
@jwt_required
def order_detail(order_id):
    """获取订单详情"""
    user_id = request.current_user_id

    order = Order.query.filter_by(id=order_id, user_id=user_id).first()
    if not order:
        raise ApiException(msg="订单不存在")

    items = OrderItem.query.filter_by(order_id=order_id).all()

    item_data = [{
        "goods_id": item.goods_id,
        "goods_name": item.goods_name,
        "goods_price": float(item.goods_price),
        "count": item.count,
        "total_price": float(item.total_price)
    } for item in items]

    status_map = {
        0: "待付款",
        1: "已付款",
        2: "已发货",
        3: "已完成",
        4: "已取消"
    }

    return success_response(data={
        "order_id": order.id,
        "total_amount": float(order.total_mount),
        "status": order.status,
        "status_text": status_map.get(order.status),
        "create_time": order.create_time.strftime("%Y-%m-%d %H:%M:%S"),
        "items": item_data
    })
