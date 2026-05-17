from backend.repository.base_repo import BaseRepo
from backend.models import Cart
from backend.extensions import db

class CartRepo(BaseRepo):
    """购物车表数据访问层"""
    model = Cart

    @classmethod
    def get_user_cart(cls, user_id):
        """获取用户购物车"""
        return cls.model.query.filter_by(user_id=user_id).all()

    @classmethod
    def get_by_user_and_goods(cls, user_id, goods_id):
        """根据用户ID和商品ID查找购物车项"""
        return cls.model.query.filter_by(user_id=user_id, goods_id=goods_id).first()

    @classmethod
    def clear_user_cart(cls, user_id):
        """清空用户购物车"""
        cls.model.query.filter_by(user_id=user_id).delete()
        db.session.commit()
