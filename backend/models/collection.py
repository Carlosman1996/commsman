from backend.models.base import *


@dataclass
class Collection(BaseRequest):
    __tablename__ = "collection"

    item_response_handler: str = "CollectionResult"

    item_id: Mapped[int] = mapped_column(Integer, ForeignKey("request.item_id", ondelete="CASCADE"), primary_key=True)

    item_type: Mapped[str] = mapped_column(String, default="Collection")


@dataclass
class CollectionResult(BaseResult):
    __tablename__ = "collection_result"

    # Initialize to None but it is non-nullable:
    request_id: Mapped[int] = mapped_column(Integer, ForeignKey("collection.item_id", ondelete="SET NULL"), nullable=False, default=None)  # Do not delete on cascade because parent result will show incorrect results

    item_type: Mapped[str] = mapped_column(String, default="Collection")
    total_ok: Mapped[int] = mapped_column(Integer, default=0)
    total_failed: Mapped[int] = mapped_column(Integer, default=0)
    total_pending: Mapped[int] = mapped_column(Integer, default=0)
