from flask import request, Blueprint
from backend.service.auth_service import AuthService
from backend.utils.response import success_response

auth_bp = Blueprint('auth', __name__, url_prefix='/api')
auth_service = AuthService()

# 用户注册
@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    user = auth_service.register(data.get('username'), data.get('password'))
    return success_response({'user_id': user.id}, "注册成功")

# 管理员注册
@auth_bp.route('/admin/register', methods=['POST'])
def admin_register():
    data = request.get_json()
    user = auth_service.admin_register(data.get('username'), data.get('password'))
    return success_response({'user_id': user.id}, "注册成功")

# 用户登录
@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    user = auth_service.login(data.get('username'), data.get('password'))
    token = user.generate_jwt_token(expires_in=7200)
    return success_response(msg="登录成功", data={'token': token, 'user': user.to_dict()})

# 管理员登录
@auth_bp.route('/admin/login', methods=['POST'])
def admin_login():
    data = request.get_json()
    user = auth_service.admin_login(data.get('username'), data.get('password'))
    token = user.generate_jwt_token(expires_in=7200)
    return success_response(msg="登录成功", data={'token': token, 'admin': user.to_dict()})

















