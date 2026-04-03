# 创建登录API接口
from flask import request, jsonify
from backend.app import app, db
from backend.models import User
from backend.utils.response import success_response, error_response
from backend.utils.exceptions import ApiException
from backend.utils.jwt_auth import jwt_required

# 用户注册
@app.route('/api/register', methods=['POST'])
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
        return success_response("注册成功", {'user_id': new_user.id})
    except Exception as e:
        db.session.rollback()
        raise ApiException("注册失败", 500)

# 用户登录
@app.route('/api/login', methods=['POST'])
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

# 获取当前用户信息（需要登录）
@app.route('/api/user/me', methods=['GET'])
@jwt_required
def get_current_user():
    user = (User.query.get(request.current_user_id))

    if not user:
        raise ApiException("用户不存在", 404)

    return success_response("获取成功", user.to_dict())






















