from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict


class OAuthUrlResponse(BaseModel):
    auth_url: str
    state: str


class SquareConnectionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    merchant_id: str
    merchant_name: Optional[str]
    country: Optional[str]
    language_code: Optional[str]
    status: Optional[str]
    environment: str
    scope: Optional[str]
    expires_at: Optional[datetime]
    connected_at: datetime
    created_at: datetime
    updated_at: datetime
    
    connection_status: str
    auto_sync_enabled: bool
    disconnected_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None
    token_revoked_at: Optional[datetime] = None


class SquareLocationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    merchant_id: str
    location_id: str
    name: Optional[str]
    business_name: Optional[str]
    country: Optional[str]
    currency: Optional[str]
    timezone: Optional[str]
    status: Optional[str]
    is_main_location: bool
    created_at: datetime
    updated_at: datetime


class SquarePaymentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    merchant_id: str
    location_id: Optional[str]
    payment_id: str
    order_id: Optional[str]
    status: Optional[str]
    source_type: Optional[str]
    amount: Optional[int]
    currency: Optional[str]
    created_at_square: Optional[datetime]
    updated_at_square: Optional[datetime]
    created_at: datetime
    updated_at: datetime


class SquareOrderRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    merchant_id: str
    location_id: Optional[str]
    order_id: str
    state: Optional[str]
    total_amount: Optional[int]
    currency: Optional[str]
    created_at_square: Optional[datetime]
    updated_at_square: Optional[datetime]
    created_at: datetime
    updated_at: datetime


class SquareRawResponse(BaseModel):
    data: dict[str, Any]


class SquareSyncSettingsUpdate(BaseModel):
    auto_sync_enabled: bool


class SquareConnectionActionResponse(BaseModel):
    merchant_id: str
    connection_status: str
    auto_sync_enabled: bool
    disconnected_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None
    token_revoked_at: Optional[datetime] = None