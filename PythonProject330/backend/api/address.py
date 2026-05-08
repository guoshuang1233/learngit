from flask import Blueprint, request
from backend.extensions import db
from backend.models import Address, User
from backend.utils.response import success_response
from backend.utils.exceptions import ApiException
from backend.utils.jwt_auth import jwt_required
from datetime import datetime

address_bp = Blueprint('address', __name__, url_prefix='/api/address')
@address_bp.route('/list', methods=['POST'])
@jwt_required
def get_address_list():
    user_id = request.current_user_id
    addresses = Address.query.filter_by(user_id=user_id).order_by(Address.is_default.desc(), Address.create_time.desc()).all()

    result = [{
        "id": addr.id,
        "receiver": addr.receiver,
        "phone": addr.phone,
        "province": addr.province,
        "city": addr.city,
        "district": addr.district,
        "detail": addr.detail,
        "is_default": addr.is_default,
        "full_address": f"{addr.province}{addr.city}{addr.district}{addr.detail}"
    }for addr in addresses]

    return success_response(data=result)

@address_bp.route('/add', methods=['POST'])
@jwt_required
def add_address():
    """添加地址"""
    user_id = request.current_user_id
    data = request.get_json()

    # strip()去掉字符串开头和结尾的空格、换行、空白符号
    receiver = data.get('receiver', '').strip()
    phone = data.get('phone', '').strip()
    province = data.get('province', '').strip()
    city = data.get('city', '').strip()
    district = data.get('district', '').strip()
    detail = data.get('detail', '').strip()
    is_default = data.get('is_default', False)

    if not receiver:
        raise ApiException( '请填写收货人', 400)
    if not phone:
        raise ApiException( '请填写手机号', 400)
    if len(phone) < 11:
        raise ApiException( '手机号长度有误', 400)
    if not province or not city or not district:
        raise ApiException( '省市区不能为空', 400)

    #.update({'字段名': 新值})
    if is_default:
        Address.query.filter_by(user_id=user_id, is_default=True).update({'is_default': False})

    new_address = Address(
        user_id=user_id,
        receiver=receiver,
        phone=phone,
        province=province,
        city=city,
        district=district,
        detail=detail,
        is_default=is_default
    )

    db.session.add(new_address)
    db.session.commit()

    return success_response(msg="地址添加成功", data={"id": new_address.id})

# 限制地址ID必须是数字，更安全（防止SQL注入、乱传参数）
@address_bp.route('/<int:address_id>', methods=['PUT'])
@jwt_required
def update_address(address_id):
    """修改地址"""
    user_id = request.current_user_id
    data = request.get_json()
    address = Address.query.filter_by(id=address_id, user_id=user_id).first()

    if not address:
        raise ApiException( '地址不存在', 404)

    data = request.get_json()
    receiver = data.get('receiver', '').strip()
    if not receiver:
        raise ApiException( '请填写收货人', 400)
    address.receiver = receiver

    if 'phone' in data:
        phone = data['phone'].strip()
        if not phone or len(phone) < 11:
            raise ApiException("手机号格式不正确", 400)
        address.phone = phone

    if 'province' in data:
        address.province = data['province'].strip()
    if 'city' in data:
        address.city = data['city'].strip()
    if 'district' in data:
        address.district = data['district'].strip()
    if 'detail' in data:
        detail = data['detail'].strip()
        if not detail:
            raise ApiException("详细地址不能为空", 400)
        address.detail = detail
    if 'is_default' in data and data['is_default']:
        Address.query.filter_by(user_id=user_id, is_default=True).update({'is_default': False})
        address.is_default = True

    db.session.commit()
    return success_response(msg="地址更新成功")

@address_bp.route('/<int:address_id>', methods=['DELETE'])
@jwt_required
def delete_address(address_id):
    """删除地址"""
    user_id = request.current_user_id
    address = Address.query.filter_by(id=address_id, user_id=user_id).first()

    if not address:
        raise ApiException( '地址不存在', 404)
    db.session.delete(address)
    db.session.commit()
    return success_response(msg='地址删除成功')

@address_bp.route('/<int:address_id>/default', methods=['POST'])
@jwt_required
def set_default_address(address_id):
    """设置默认地址"""
    user_id = request.current_user_id
    address = Address.query.filter_by(id=address_id, user_id=user_id).first()
    if not address:
        raise ApiException( '地址不存在', 404)
    Address.query.filter_by(user_id=user_id, is_default=True).update({'is_default': False})
    address.is_default = True

    db.session.commit()

    return success_response(msg="默认地址设置成功")

@address_bp.route('/default', methods=['GET'])
@jwt_required
def get_default_address():
    """获取默认地址"""
    user_id = request.current_user_id
    address = Address.query.filter_by(user_id=user_id).order_by(
        Address.is_default.desc(),
        Address.create_time.desc()
    ).first()

    if not address:
        return success_response(data=None)

    return success_response(data={
        "id": address.id,
        "receiver": address.receiver,
        "phone": address.phone,
        "province": address.province,
        "city": address.city,
        "district": address.district,
        "detail": address.detail,
        "is_default": address.is_default,
        "full_address": f"{address.province}{address.city}{address.district}{address.detail}"
    })



