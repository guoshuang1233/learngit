from backend.repository.base_repo import BaseRepo
from backend.models import Order, OrderItem
from backend.extensions import db

class OrderRepo(BaseRepo):
    """订单表数据访问层"""
    model = Order

    @classmethod
    def create_order_with_items(cls, order_id, user_id, total_amount, address_id):
        """创建订单主表"""
        from datetime import datetime
        order = Order(
            id=order_id, user_id=user_id, total_amount=total_amount,
            status=0, address_id=address_id, create_time=datetime.now()
        )
        db.session.add(order)
        db.session.commit()
        return order

    @classmethod
    def get_user_orders(cls, user_id, page=1, size=20):
        """获取用户订单列表"""
        return cls.model.query.filter_by(user_id=user_id).order_by(
            cls.model.create_time.desc()
        ).paginate(page=page, per_page=size, error_out=False)
