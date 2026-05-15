from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
)
from sqlmodel import Field, SQLModel
from sqlalchemy import Boolean, Column, DateTime, JSON, String, Text

def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class SquareConnection(SQLModel, table=True):
    __tablename__ = "square_connections"

    id: Optional[int] = Field(default=None, primary_key=True)

    merchant_id: str = Field(
        sa_column=Column(String, unique=True, index=True, nullable=False)
    )

    merchant_name: Optional[str] = Field(default=None, sa_column=Column(String))
    country: Optional[str] = Field(default=None, sa_column=Column(String))
    language_code: Optional[str] = Field(default=None, sa_column=Column(String))
    status: Optional[str] = Field(default=None, sa_column=Column(String))

    environment: str = Field(default="sandbox", sa_column=Column(String, nullable=False))

    access_token: str = Field(sa_column=Column(Text, nullable=False))
    refresh_token: Optional[str] = Field(default=None, sa_column=Column(Text))
    token_type: Optional[str] = Field(default=None, sa_column=Column(String))
    scope: Optional[str] = Field(default=None, sa_column=Column(Text))
    expires_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), nullable=True),
    )

    raw_token_json: dict[str, Any] = Field(
        default_factory=dict,
        sa_column=Column(JSON, nullable=False),
    )
    raw_merchant_json: dict[str, Any] = Field(
        default_factory=dict,
        sa_column=Column(JSON, nullable=False),
    )

    connected_at: datetime = Field(
        default_factory=utc_now,
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
    created_at: datetime = Field(
        default_factory=utc_now,
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
    updated_at: datetime = Field(
        default_factory=utc_now,
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
    connection_status: str = Field(
        default="connected",
        sa_column=Column(String, nullable=False),
    )
    auto_sync_enabled: bool = Field(
        default=True,
        sa_column=Column(Boolean, nullable=False),
    )
    disconnected_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), nullable=True),
    )
    deleted_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), nullable=True),
    )
    token_revoked_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), nullable=True),
    )


class SquareLocation(SQLModel, table=True):
    __tablename__ = "square_locations"
    __table_args__ = (
        UniqueConstraint(
            "merchant_id",
            "location_id",
            name="uq_square_locations_merchant_location",
        ),
    )

    id: Optional[int] = Field(default=None, primary_key=True)

    merchant_id: str = Field(
        sa_column=Column(
            String,
            ForeignKey("square_connections.merchant_id"),
            index=True,
            nullable=False,
        )
    )

    location_id: str = Field(sa_column=Column(String, index=True, nullable=False))

    name: Optional[str] = Field(default=None, sa_column=Column(String))
    business_name: Optional[str] = Field(default=None, sa_column=Column(String))
    country: Optional[str] = Field(default=None, sa_column=Column(String))
    currency: Optional[str] = Field(default=None, sa_column=Column(String))
    timezone: Optional[str] = Field(default=None, sa_column=Column(String))
    status: Optional[str] = Field(default=None, sa_column=Column(String))
    is_main_location: bool = Field(
        default=False,
        sa_column=Column(Boolean, nullable=False),
    )

    raw_json: dict[str, Any] = Field(
        default_factory=dict,
        sa_column=Column(JSON, nullable=False),
    )

    created_at: datetime = Field(
        default_factory=utc_now,
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
    updated_at: datetime = Field(
        default_factory=utc_now,
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )


class SquarePayment(SQLModel, table=True):
    __tablename__ = "square_payments"
    __table_args__ = (
        UniqueConstraint(
            "merchant_id",
            "payment_id",
            name="uq_square_payments_merchant_payment",
        ),
    )

    id: Optional[int] = Field(default=None, primary_key=True)

    merchant_id: str = Field(
        sa_column=Column(
            String,
            ForeignKey("square_connections.merchant_id"),
            index=True,
            nullable=False,
        )
    )

    location_id: Optional[str] = Field(default=None, sa_column=Column(String, index=True))
    payment_id: str = Field(sa_column=Column(String, index=True, nullable=False))
    order_id: Optional[str] = Field(default=None, sa_column=Column(String, index=True))

    status: Optional[str] = Field(default=None, sa_column=Column(String))
    source_type: Optional[str] = Field(default=None, sa_column=Column(String))

    amount: Optional[int] = Field(default=None, sa_column=Column(Integer))
    currency: Optional[str] = Field(default=None, sa_column=Column(String))

    created_at_square: Optional[datetime] = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), nullable=True),
    )
    updated_at_square: Optional[datetime] = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), nullable=True),
    )

    raw_json: dict[str, Any] = Field(
        default_factory=dict,
        sa_column=Column(JSON, nullable=False),
    )

    created_at: datetime = Field(
        default_factory=utc_now,
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
    updated_at: datetime = Field(
        default_factory=utc_now,
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )


class SquareOrder(SQLModel, table=True):
    __tablename__ = "square_orders"
    __table_args__ = (
        UniqueConstraint(
            "merchant_id",
            "order_id",
            name="uq_square_orders_merchant_order",
        ),
    )

    id: Optional[int] = Field(default=None, primary_key=True)

    merchant_id: str = Field(
        sa_column=Column(
            String,
            ForeignKey("square_connections.merchant_id"),
            index=True,
            nullable=False,
        )
    )

    location_id: Optional[str] = Field(default=None, sa_column=Column(String, index=True))
    order_id: str = Field(sa_column=Column(String, index=True, nullable=False))

    state: Optional[str] = Field(default=None, sa_column=Column(String))

    total_amount: Optional[int] = Field(default=None, sa_column=Column(Integer))
    currency: Optional[str] = Field(default=None, sa_column=Column(String))

    created_at_square: Optional[datetime] = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), nullable=True),
    )
    updated_at_square: Optional[datetime] = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), nullable=True),
    )

    raw_json: dict[str, Any] = Field(
        default_factory=dict,
        sa_column=Column(JSON, nullable=False),
    )

    created_at: datetime = Field(
        default_factory=utc_now,
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
    updated_at: datetime = Field(
        default_factory=utc_now,
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )