from flask import Blueprint, request
from backend.service.address_service import AddressService
from backend.utils.response import success_response
from backend.utils.jwt_auth import jwt_required

address_bp = Blueprint('address', __name__, url_prefix='/api/address')
address_service = AddressService()

@address_bp.route('/list', methods=['POST'])
@jwt_required
def get_address_list():
    user_id = request.current_user_id
    addresses = address_service.get_list(user_id)
    result = [{
        "id": addr.id, "receiver": addr.receiver, "phone": addr.phone,
        "province": addr.province, "city": addr.city, "district": addr.district,
        "detail": addr.detail, "is_default": addr.is_default,
        "full_address": f"{addr.province}{addr.city}{addr.district}{addr.detail}"
    } for addr in addresses]
    return success_response(data=result)

@address_bp.route('', methods=['POST'])
@jwt_required
def add_address():
    user_id = request.current_user_id
    data = request.get_json()
    addr = address_service.create(
        user_id=user_id, receiver=data.get('receiver'), phone=data.get('phone'),
        province=data.get('province'), city=data.get('city'), district=data.get('district'),
        detail=data.get('detail'), is_default=data.get('is_default', False)
    )
    return success_response(msg="地址添加成功", data={"id": addr.id})

@address_bp.route('/<int:address_id>', methods=['PUT'])
@jwt_required
def update_address(address_id):
    user_id = request.current_user_id
    data = request.get_json()
    address_service.update(user_id, address_id, **data)
    return success_response(msg="地址更新成功")

@address_bp.route('/<int:address_id>', methods=['DELETE'])
@jwt_required
def delete_address(address_id):
    user_id = request.current_user_id
    address_service.delete(user_id, address_id)
    return success_response(msg='地址删除成功')

@address_bp.route('/<int:address_id>/default', methods=['POST'])
@jwt_required
def set_default_address(address_id):
    user_id = request.current_user_id
    address_service.set_default(user_id, address_id)
    return success_response(msg="默认地址设置成功")

@address_bp.route('/default', methods=['GET'])
@jwt_required
def get_default_address():
    user_id = request.current_user_id
    addr = address_service.get_default(user_id)
    if not addr:
        return success_response(data=None)
    return success_response(data={
        "id": addr.id, "receiver": addr.receiver, "phone": addr.phone,
        "province": addr.province, "city": addr.city, "district": addr.district,
        "detail": addr.detail, "is_default": addr.is_default,
        "full_address": f"{addr.province}{addr.city}{addr.district}{addr.detail}"
    })



