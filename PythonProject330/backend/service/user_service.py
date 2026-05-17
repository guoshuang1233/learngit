from backend.repository.user_repo import UserRepo
from backend.utils.exceptions import ApiException


class UserService:
    """用户业务逻辑层"""

    def get_info(self, user_id):
        """获取用户信息"""
        user = UserRepo.get_by_id(user_id)
        if not user:
            raise ApiException("用户不存在", 404)
        return user

    def update_info(self, user_id, **kwargs):
        """更新用户信息"""
        user = UserRepo.get_by_id(user_id)
        if not user:
            raise ApiException("用户不存在", 404)

        if 'phone' in kwargs and kwargs['phone']:
            if len(kwargs['phone']) < 11:
                raise ApiException("手机号格式不正确", 400)

        return UserRepo.update(user, **kwargs)
