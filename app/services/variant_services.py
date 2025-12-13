from typing import List

from app.models import Variant


class VariantService:
    @staticmethod
    def get_by_author(author_id: int) -> List[Variant]:
        return (
            Variant.query
            .filter_by(author_id=author_id)
            .order_by(Variant.created_at.desc())
            .all()
        )
