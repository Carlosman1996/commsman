from backend.models.base import *


@dataclass
class Request(BaseItem):
    __tablename__ = "request"

    item_type: Mapped[str] = mapped_column(String, default="Request")
    request_type_handler: Mapped[int] = mapped_column(String, default=None)
