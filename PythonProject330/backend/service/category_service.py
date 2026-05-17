from backend.repository.category_repo import CategoryRepo
from backend.utils.exceptions import ApiException


class CategoryService:
    """分类业务逻辑层"""

    def get_all(self):
        """获取所有分类"""
        return CategoryRepo.get_all()
