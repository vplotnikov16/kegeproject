from sqlalchemy import LargeBinary
from sqlalchemy.dialects.mysql import MEDIUMBLOB

from app.extensions import db

Binary = LargeBinary().with_variant(MEDIUMBLOB, "mysql")


class IModel(db.Model):
    __abstract__ = True

    @classmethod
    def view_name(cls) -> str:
        raise NotImplementedError
