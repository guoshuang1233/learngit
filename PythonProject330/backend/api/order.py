from flask import Blueprint, request
from sqlalchemy import or_
from backend.extensions import db
from backend.models import Order, OrderItem, Cart, Goods
from backend.utils.response import success_response
from backend.utils.exceptions import ApiException
from backend.utils.jwt_auth import jwt_required
from datetime import datetime, timedelta
import uuid

STATUS_MAP = {
    0: "待付款",
    1: "待发货",
    2: "运输中",
    3: "已完成",
    4: "已取消",
}

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


def _serialize_order_row(order):
    items = OrderItem.query.filter_by(order_id=order.id).all()
    total_qty = sum(i.count for i in items)
    previews = []
    for oi in items[:5]:
        g = Goods.query.get(oi.goods_id)
        previews.append({
            "goods_id": oi.goods_id,
            "goods_name": oi.goods_name,
            "count": oi.count,
            "img": (g.img if g and g.img else "") or "",
        })
    return {
        "order_id": order.id,
        "total_amount": float(order.total_amount),
        "status": order.status,
        "status_text": STATUS_MAP.get(order.status, "未知状态"),
        "create_time": order.create_time.strftime("%Y-%m-%d %H:%M:%S") if order.create_time else None,
        "item_count": total_qty,
        "items_preview": previews,
    }


@order_bp.route("/list", methods=["GET"])
@jwt_required
def order_list():
    """获取订单列表（支持关键词、时间范围、状态 Tab）"""
    user_id = request.current_user_id
    keyword = (request.args.get("keyword") or "").strip()
    months = request.args.get("months", default="6")
    tab = (request.args.get("tab") or "all").strip().lower()

    try:
        months_int = int(months)
    except ValueError:
        months_int = 6

    base_q = Order.query.filter_by(user_id=user_id)
    if months_int > 0:
        since = datetime.now() - timedelta(days=31 * months_int)
        base_q = base_q.filter(Order.create_time >= since)

    counts = {
        "all": base_q.count(),
        "unpaid": base_q.filter(Order.status == 0).count(),
        "transit": base_q.filter(Order.status == 2).count(),
        "return": base_q.filter(Order.status == 3).count(),
    }

    q = base_q
    if tab == "unpaid":
        q = q.filter(Order.status == 0)
    elif tab == "transit":
        q = q.filter(Order.status == 2)
    elif tab == "return":
        q = q.filter(Order.status == 3)

    if keyword:
        like = f"%{keyword}%"
        match_items = db.session.query(OrderItem.order_id).filter(
            OrderItem.goods_name.like(like)
        ).distinct()
        q = q.filter(or_(Order.id.like(like), Order.id.in_(match_items)))

    orders = q.order_by(Order.create_time.desc()).all()
    result = [_serialize_order_row(o) for o in orders]

    return success_response(data={"list": result, "counts": counts})


@order_bp.route("/detail/<order_id>", methods=["GET"])
@jwt_required
def order_detail(order_id):
    """获取订单详情"""
    user_id = request.current_user_id

    order = Order.query.filter_by(id=order_id, user_id=user_id).first()
    if not order:
        raise ApiException("订单不存在", 404)

    items = OrderItem.query.filter_by(order_id=order_id).all()

    item_data = []
    for item in items:
        g = Goods.query.get(item.goods_id)
        item_data.append({
            "goods_id": item.goods_id,
            "goods_name": item.goods_name,
            "goods_price": float(item.goods_price),
            "count": item.count,
            "total_price": float(item.total_price),
            "goods_img": (g.img if g and g.img else "") or "",
        })

    return success_response(data={
        "order_id": order.id,
        "total_amount": float(order.total_amount),
        "status": order.status,
        "status_text": STATUS_MAP.get(order.status),
        "create_time": order.create_time.strftime("%Y-%m-%d %H:%M:%S"),
        "items": item_data
    })
