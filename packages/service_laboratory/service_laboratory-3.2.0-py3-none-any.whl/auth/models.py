from advanced_alchemy.base import UUIDAuditBase
from sqlalchemy.orm import mapped_column, Mapped


class UserModel(UUIDAuditBase):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(unique=True)
