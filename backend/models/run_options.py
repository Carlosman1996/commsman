from backend.models.base import *


@dataclass
class RunOptions(BaseItem):
    __tablename__ = "run_options"

    item_type: Mapped[str] = mapped_column(String, default="RunOptions")
    polling: Mapped[bool] = mapped_column(Boolean, default=False)
    polling_interval: Mapped[int] = mapped_column(Integer, default=1)
    delayed_start: Mapped[int] = mapped_column(Integer, default=0)
