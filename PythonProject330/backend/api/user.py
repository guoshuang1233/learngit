from flask import Blueprint, request
from backend.service.user_service import UserService
from backend.utils.response import success_response
from backend.utils.jwt_auth import jwt_required

user_bp = Blueprint('user', __name__, url_prefix='/api/user')
user_service = UserService()

@user_bp.route('/me', methods=['GET'])
@jwt_required
def get_current_user():
    user = user_service.get_info(request.current_user_id)
    return success_response(msg="获取成功", data=user.to_dict())

@user_bp.route('/me', methods=['PUT'])
@jwt_required
def update_user():
    data = request.get_json()
    user = user_service.update_info(request.current_user_id, **data)
    return success_response(msg="更新成功", data=user.to_dict())
