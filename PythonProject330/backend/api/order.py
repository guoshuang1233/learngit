from flask import Blueprint, request
from backend.extensions import db
from backend.models import Order, OrderItem, Cart, Goods
from backend.utils.response import success_response
from backend.utils.exceptions import ApiException
from backend.utils.jwt_auth import jwt_required
from datetime import datetime
import  uuid # 生成一个唯一的ID标识

order_bp = Blueprint("order", __name__, url_prefix="/api/order")

@order_bp.route("/create", methods=["POST"])
@jwt_required
# 先循环购物车商品 → 生成订单明细 → 最后才生成订单主记录
def create_order():
    """创建订单（虚拟卡支付）"""
    # 虚拟卡体现在status=1--直接标记”已付款“，下单直接成功
    user_id = request.current_user_id
    cart_items = Cart.query.filter_by(user_id=user_id, is_selected=True).all()
    # 创建订单前校验购物车是否为空，是为了避免并发操作、前端状态不同步、非法接口调用或商品数据异常导致创建无效订单，确保业务流程健壮性与数据一致性。
    if not cart_items:
        raise ApiException("购物车为空", 400)

    total_amount = 0
    order_items = []
    for cart in cart_items:
        goods = cart.goods
        # 购物车是老数据，商品是实时数据，所以需要校验
        if not goods:
            raise ApiException("商品不存在", 404)

        subtotal = float(goods.price) * cart.count
        total_amount += subtotal
        order_items.append({
            "goods_id": goods.id,
            "goods_name": goods.name,
            "goods_price": float(goods.price),
            "count": cart.count,
            "total_price": subtotal # 记录的商品小计加起来的价格，订单总额记录在order主表中
        })
        # uuid=全球唯一ID，.hex=转成字符串，[:6]=只取前6位
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
            for item in order_items:
                order_item = OrderItem(
                    order_id=order_id,
                    goods_id=item["goods_id"],
                    goods_name=item["goods_name"],
                    goods_price=item["goods_price"],
                    count=item["count"],
                    total_price=item["total_price"]
                )
                db.session.add(order_item)
                # 删除购物车，防止重复下单
                for cart in cart_items:
                    db.session.delete(cart)

                db.session.commit()
                return success_response(msg="下单成功", data={
                     "order_id": order_id,
                     "total_amount": total_amount,
                     "status": "已付款"
                })
        except Exception as e:
            db.session.rollback()
            raise ApiException("下单失败", 500)

@order_bp.route("/list", methods=["GET"])
@jwt_required
def order_list():
    """获取订单列表"""
    user_id = request.current_user_id

    # 查询当前用户的所有订单，按创建时间倒序
    orders = Order.query.filter_by(user_id=user_id).order_by(Order.create_time.desc()).all()

    # 订单状态文案映射,因为前端不能显示数字，需要用中文
    status_map = {
        0: "待付款",
        1: "已付款", # 现在表中是写死的数字1
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
    # 查询当前用户指定订单(查订单主表)
    order = Order.query.filter_by(id=order_id, user_id=user_id).first()
    if not order:
        raise ApiException(msg="订单不存在")
    # 查订单商品明细（只有详情才需要）
    items = OrderItem.query.filter_by(order_id=order_id).all()
    # 列表推导式
    item_data = [{
        "goods_id": item.goods_id,
        "goods_name": item.goods_name,
        "goods_price": float(item.goods_price),
        "count": item.count,
        "total_price": float(item.total_price)
    }for item in items]

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
        "items": item_data # 只有详情才返回商品！
    })

















