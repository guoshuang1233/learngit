from flask import Blueprint, request
from backend.extensions import db
from backend.models import User
from backend.utils.response import success_response
from backend.utils.exceptions import ApiException
from backend.utils.jwt_auth import jwt_required

user_bp = Blueprint('user', __name__, url_prefix='/api/user')

@user_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()

    if not data or not data.get('username') or not data.get('password'):
        raise ApiException("用户名和密码不能为空", 400)

    username = data.get('username')
    password = data.get('password')

    existing_user = User.query.filter_by(username=username).first()
    if existing_user:
        raise ApiException("用户名已存在", 400)

    new_user = User(username=username)
    new_user.set_password(password)

    try:
        db.session.add(new_user)
        db.session.commit()
        return success_response("注册成功", {'user_id': new_user.id})
    except Exception as e:
        db.session.rollback()
        raise ApiException("注册失败", 500)
        db,session.remove()

# 获取当前用户信息（需要登录）
@user_bp.route('/me', methods=['GET'])
@jwt_required
def get_current_user():
    user = User.query.get(request.current_user_id)
    # 防御性编程：虽用户注册后token未过期，但用户被管理员删除了，就会返回None
    if not user:
        raise ApiException("用户不存在", 404)

    return success_response(msg="获取成功", data=user.to_dict())

# 更新当前用户信息（需要登录）
@user_bp.route('/me', methods=['PUT'])
@jwt_required
def update_user():
    user = User.query.get(request.current_user_id)

    if not user:
        raise ApiException("用户不存在", 404)

    data = request.get_json()

    if data.get('username'):
        existing = User.query.filter_by(username=data.get('username')).first()
        if existing and existing.id != user.id:
            raise ApiException("用户名已被使用", 400)
        user.username = data.get('username')

    if data.get('phone'):
        user.phone = data.get('phone')

    if data.get('email'):
        user.email = data.get('email')

    if data.get('avatar'):
        user.avatar = data.get('avatar')

    db.session.commit()

    return success_response(msg="更新成功", data=user.to_dict())
