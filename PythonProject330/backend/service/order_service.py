from backend.repository.order_repo import OrderRepo
from backend.utils.exceptions import ApiException


class OrderService:
    """订单业务逻辑层"""

    def get_user_orders(self, user_id, page=1, size=20):
        """获取用户订单列表"""
        return OrderRepo.get_user_orders(user_id, page, size)

    def get_order_detail(self, user_id, order_id):
        """获取订单详情"""
        order = OrderRepo.get_by_id(order_id)
        if not order or order.user_id != user_id:
            raise ApiException("订单不存在", 404)
        return order
