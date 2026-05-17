from backend.repository.base_repo import BaseRepo
from backend.models import Category


class CategoryRepo(BaseRepo):
    """分类表数据访问层"""
    model = Category
