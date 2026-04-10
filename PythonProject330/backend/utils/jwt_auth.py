# 创建JWT装饰器（用于保护需要登录的接口）
from functools import wraps
from flask import request, jsonify


def jwt_required(f):
    """
    JWT 认证装饰器
    用于保护需要登录的API接口
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        from backend.models import User
        # 从请求头获取token
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({
                'code': 401,
                'msg': '缺少认证 token',
                'data': None
            }), 401
        # 移除"Bearer"前缀（如果有）
        if token.startswith('Bearer '):
            token = token[7:]
        # 验证 token
        payload = User.verify_jwt_token(token)
        if not payload:
            return jsonify({
                'code': 401,
                'msg': '无效的认证 token',
                'data': None
            }), 401

        # 将用户信息添加到请求上下文
        request.current_user_id = payload['user_id']
        request.current_username = payload['username']

        return f(*args, **kwargs)

    # 返回【已经加上登录验证】的包装后函数、必须写，不写装饰器直接报废
    return decorated_function