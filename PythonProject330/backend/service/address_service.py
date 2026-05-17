from backend.repository.address_repo import AddressRepo
from backend.utils.exceptions import ApiException


class AddressService:
    """地址业务逻辑层"""

    def get_list(self, user_id):
        """获取地址列表"""
        return AddressRepo.get_user_addresses(user_id)

    def get_default(self, user_id):
        """获取默认地址"""
        addresses = AddressRepo.get_user_addresses(user_id)
        for addr in addresses:
            if addr.is_default:
                return addr
        return addresses[0] if addresses else None

    def create(self, user_id, receiver, phone, province, city, district, detail, is_default=False):
        """添加地址"""
        if not receiver or not receiver.strip():
            raise ApiException("请填写收货人", 400)
        if not phone or len(phone) < 11:
            raise ApiException("手机号格式不正确", 400)
        if not province or not city or not district:
            raise ApiException("省市区不能为空", 400)
        if not detail or not detail.strip():
            raise ApiException("详细地址不能为空", 400)

        if is_default:
            AddressRepo.set_default(user_id, None)

        return AddressRepo.create(
            user_id=user_id,
            receiver=receiver.strip(),
            phone=phone.strip(),
            province=province.strip(),
            city=city.strip(),
            district=district.strip(),
            detail=detail.strip(),
            is_default=is_default
        )

    def update(self, user_id, address_id, **kwargs):
        """更新地址"""
        address = AddressRepo.get_by_id(address_id)
        if not address or address.user_id != user_id:
            raise ApiException("地址不存在", 404)

        if 'phone' in kwargs and (not kwargs['phone'] or len(kwargs['phone']) < 11):
            raise ApiException("手机号格式不正确", 400)
        if 'receiver' in kwargs and not kwargs['receiver']:
            raise ApiException("请填写收货人", 400)
        if 'detail' in kwargs and not kwargs['detail']:
            raise ApiException("详细地址不能为空", 400)

        if kwargs.get('is_default'):
            AddressRepo.set_default(user_id, address_id)

        return AddressRepo.update(address, **kwargs)

    def delete(self, user_id, address_id):
        """删除地址"""
        address = AddressRepo.get_by_id(address_id)
        if not address or address.user_id != user_id:
            raise ApiException("地址不存在", 404)
        AddressRepo.delete(address)

    def set_default(self, user_id, address_id):
        """设置默认地址"""
        address = AddressRepo.get_by_id(address_id)
        if not address or address.user_id != user_id:
            raise ApiException("地址不存在", 404)
        AddressRepo.set_default(user_id, address_id)
