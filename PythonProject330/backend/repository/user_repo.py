from backend.repository.base_repo import BaseRepo
from backend.models import User

class UserRepo(BaseRepo):
    model = User

    @classmethod
    def get_by_username(cls, username):
        return cls.model.query.filter_by(username=username).first()