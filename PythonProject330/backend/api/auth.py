# 创建登录API接口
from flask import request, jsonify, Blueprint
from backend.extensions import db
from backend.models import User
from backend.utils.response import success_response, error_response
from backend.utils.exceptions import ApiException
from backend.utils.jwt_auth import jwt_required



auth_bp = Blueprint('auth', __name__, url_prefix='/api')
# 用户注册
@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()

    if not data or not data.get('username') or not data.get('password'):
        raise ApiException("用户名和密码不能为空", 400)

    username = data.get('username')
    password = data.get('password')

    # 检查用户是否存在
    # 查唯一数据（用户名、手机号、ID）用.first（）；查多条数据（列表，订单）用.all()
    existing_user = User.query.filter_by(username=username).first()
    if existing_user:
        raise ApiException("用户名已存在", 400)

    # 创建新用户
    new_user = User(username=username)
    new_user.set_password(password)

    try:
        db.session.add(new_user)
        db.session.commit()
        db.session.remove()
        return success_response("注册成功", {'user_id': new_user.id})
    except Exception as e:
        db.session.rollback()
        raise ApiException("注册失败", 500)

# 用户登录
@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    if not data or not data.get('username') or not data.get('password'):
        raise ApiException("用户名和密码不能为空", 400)

    username = data.get('username')
    password = data.get('password')

    # 查找用户
    user = User.query.filter_by(username=username).first()

    if not user or not user.check_password(password):
        raise ApiException("用户名或密码错误", 401)

    # 生成 JWT token
    token = user.generate_jwt_token(expires_in=7200)  # 2 小时过期

    return success_response(msg = "登录成功", data = {
        'token': token,
        'user': user.to_dict()
    })





















