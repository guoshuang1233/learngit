from flask import Blueprint
from backend.service.category_service import CategoryService
from backend.utils.response import success_response

category_bp = Blueprint('category', __name__, url_prefix='/api')
category_service = CategoryService()

@category_bp.route('/category', methods=['GET'])
def get_category():
    categories = category_service.get_all()
    result = [{"id": c.id, "name": c.name} for c in categories]
    return success_response(data=result)