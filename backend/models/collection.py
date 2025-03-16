from backend.models.base import *


@dataclass
class Collection(BaseRequest):
    __tablename__ = "collection"

    item_response_handler: str = "CollectionResult"

    item_type: Mapped[str] = mapped_column(String, default="Collection")


@dataclass
class CollectionResult(BaseResult):
    __tablename__ = "collection_result"

    collection_id: Mapped[int] = mapped_column(Integer, ForeignKey('collection.id'))

    item_type: Mapped[str] = mapped_column(String, default="Collection")
    total_ok: Mapped[int] = mapped_column(Integer, default=0)
    total_failed: Mapped[int] = mapped_column(Integer, default=0)
    total_pending: Mapped[int] = mapped_column(Integer, default=0)
