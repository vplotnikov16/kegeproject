from app.admin.base_view import SecureModelView
from app.models import VariantTask


class VariantAdmin(SecureModelView):
    column_list = ['id', 'source', 'author', 'created_at', 'duration']
    inline_models = [(VariantTask, {"form_columns": ['id', 'task', 'order']})]
