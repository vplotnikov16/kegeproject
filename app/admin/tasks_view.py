from wtforms import TextAreaField

from app.admin.base_view import SecureModelView


class TaskAdmin(SecureModelView):
    form_overrides = {'statement_html': TextAreaField}
