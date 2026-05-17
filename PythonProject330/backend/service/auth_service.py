from backend.repository.user_repo import UserRepo
from backend.utils.exceptions import ApiException


class AuthService:
    """认证业务逻辑层"""

    def login(self, username, password):
        """用户登录"""
        if not username or not password:
            raise ApiException("用户名和密码不能为空", 400)

        user = UserRepo.get_by_username(username)
        if not user or not user.check_password(password):
            raise ApiException("用户名或密码错误", 401)

        if user.role != 0:
            raise ApiException("该账号不是普通用户，请使用后台登录", 403)

        return user

    def admin_login(self, username, password):
        """管理员登录"""
        if not username or not password:
            raise ApiException("用户名和密码不能为空", 400)

        user = UserRepo.get_by_username(username)
        if not user or not user.check_password(password):
            raise ApiException("用户名或密码错误", 401)

        if user.role != 1:
            raise ApiException("该账号不是管理员，请使用普通用户登录", 403)

        return user

    def register(self, username, password):
        """用户注册"""
        if not username or not password:
            raise ApiException("用户名和密码不能为空", 400)

        if UserRepo.get_by_username(username):
            raise ApiException("用户名已存在", 400)

        user = UserRepo.create(username=username, role=0)
        user.set_password(password)
        return user

    def admin_register(self, username, password):
        """管理员注册"""
        if not username or not password:
            raise ApiException("用户名和密码不能为空", 400)

        if UserRepo.get_by_username(username):
            raise ApiException("用户名已存在", 400)

        user = UserRepo.create(username=username, role=1)
        user.set_password(password)
        return user
