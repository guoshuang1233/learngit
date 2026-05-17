from backend.repository.base_repo import BaseRepo
from backend.models import Address
from backend.extensions import db


class AddressRepo(BaseRepo):
    """地址表数据访问层"""
    model = Address

    @classmethod
    def get_user_addresses(cls, user_id):
        """获取用户地址列表（默认地址排在前面）"""
        return cls.model.query.filter_by(user_id=user_id).order_by(
            Address.is_default.desc(), Address.create_time.desc()).all()

    @classmethod
    def set_default(cls, user_id, address_id):
        """设置默认地址"""
        # 先取消该用户所有默认地址
        cls.model.query.filter_by(user_id=user_id, is_default=True).update({'is_default': False})
        # 再设置新的默认地址
        addr = cls.get_by_id(address_id)
        if addr:
            addr.is_default = True
            db.session.commit()
