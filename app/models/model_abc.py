from app.extensions import db


class IModel(db.Model):
    __abstract__ = True

    @classmethod
    def view_name(cls) -> str:
        raise NotImplementedError
