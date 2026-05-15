from sqlmodel import SQLModel

from app.db.session import engine

# Import models here so SQLModel knows the tables before create_all()
from app.models.square_connection import (  # noqa: F401
    SquareConnection,
    SquareLocation,
    SquareOrder,
    SquarePayment,
)


def init_db() -> None:
    SQLModel.metadata.create_all(engine)