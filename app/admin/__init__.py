from app.models import *
from .base_view import SecureModelView
from .users_view import UserAdmin
from .tasks_view import TaskAdmin
from .variant_view import VariantAdmin
from app.extensions import db

mapping = {
    User: UserAdmin,
    Task: TaskAdmin,
    Variant: VariantAdmin,
}


def get_model_view(model: db.Model):
    view = mapping.get(model, SecureModelView)
    return view
