from backend.models.base import *


@dataclass
class Client(BaseItem):
    __tablename__ = "client"

    item_type: Mapped[str] = mapped_column(String, default="Client")
    client_type_handler: Mapped[int] = mapped_column(String, default=None)
