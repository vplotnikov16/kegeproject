from app import models
from app.extensions import db
from .base_view import SecureModelView
from .users_view import UserAdmin
from .tasks_view import TaskAdmin
from .variant_view import VariantAdmin

mapping = {
    models.User: UserAdmin,
    models.Task: TaskAdmin,
    models.Variant: VariantAdmin,
}


def get_model_view(model: db.Model):
    view = mapping.get(model, SecureModelView)
    return view
