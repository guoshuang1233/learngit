from backend.repository.user_repo import UserRepo
from backend.repository.cart_repo import CartRepo
from backend.repository.goods_repo import GoodsRepo
from backend.repository.order_repo import OrderRepo
from backend.utils.exceptions import ApiException
from backend.extensions import db
from datetime import datetime
import uuid


class CartService:
    """购物车业务逻辑层"""

    def get_list(self, user_id):
        """获取购物车列表"""
        return CartRepo.get_user_cart(user_id)

    def add(self, user_id, goods_id, count=1):
        """添加商品到购物车"""
        goods = GoodsRepo.get_by_id(goods_id)
        if not goods:
            raise ApiException("商品不存在", 404)
        if goods.stock < count:
            raise ApiException("库存不足", 400)

        cart_item = CartRepo.get_by_user_and_goods(user_id, goods_id)
        if cart_item:
            return CartRepo.update(cart_item, count=cart_item.count + count)
        else:
            return CartRepo.create(user_id=user_id, goods_id=goods_id, count=count)

    def update(self, user_id, cart_id, count):
        """更新购物车数量"""
        cart_item = CartRepo.get_by_id(cart_id)
        if not cart_item or cart_item.user_id != user_id:
            raise ApiException("购物车项不存在", 404)
        if count <= 0:
            return self.delete(user_id, cart_id)
        goods = GoodsRepo.get_by_id(cart_item.goods_id)
        if goods and goods.stock < count:
            raise ApiException("库存不足", 400)
        return CartRepo.update(cart_item, count=count)

    def delete(self, user_id, cart_id):
        """删除购物车项"""
        cart_item = CartRepo.get_by_id(cart_id)
        if not cart_item or cart_item.user_id != user_id:
            raise ApiException("购物车项不存在", 404)
        CartRepo.delete(cart_item)

    def clear(self, user_id):
        """清空购物车"""
        CartRepo.clear_user_cart(user_id)

    def checkout(self, user_id, address_id):
        """结算下单"""
        cart_items = CartRepo.get_user_cart(user_id)
        if not cart_items:
            raise ApiException("购物车为空", 400)

        total_amount = 0
        order_items_data = []

        for cart in cart_items:
            goods = GoodsRepo.get_by_id(cart.goods_id)
            if not goods:
                raise ApiException(f"商品{cart.goods_id}不存在", 400)
            if goods.stock < cart.count:
                raise ApiException(f"商品{goods.name}库存不足", 400)

            subtotal = float(goods.price) * cart.count
            total_amount += subtotal
            order_items_data.append({
                "goods_id": goods.id,
                "goods_name": goods.name,
                "goods_price": float(goods.price),
                "count": cart.count,
                "total_price": subtotal
            })

        # 原子操作扣减库存
        for item in order_items_data:
            result = db.session.execute(
                db.text("UPDATE goods SET stock = stock - :count WHERE id = :goods_id AND stock >= :count"),
                {"count": item["count"], "goods_id": item["goods_id"]}
            )
            if result.rowcount == 0:
                raise ApiException(f"商品{item['goods_name']}库存不足，下单失败", 400)

        # 创建订单
        order_id = datetime.now().strftime("%Y%m%d%H%M%S") + uuid.uuid4().hex[:6]
        order = OrderRepo.create_order_with_items(
            order_id=order_id,
            user_id=user_id,
            total_amount=total_amount,
            address_id=address_id
        )

        # 添加订单明细
        for item_data in order_items_data:
            from backend.models import OrderItem
            order_item = OrderItem(
                order_id=order.id,
                goods_id=item_data["goods_id"],
                goods_name=item_data["goods_name"],
                goods_price=item_data["goods_price"],
                count=item_data["count"],
                total_price=item_data["total_price"]
            )
            db.session.add(order_item)
        db.session.commit()

        # 清空购物车
        CartRepo.clear_user_cart(user_id)

        return order
