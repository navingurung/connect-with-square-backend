from datetime import datetime, timezone
from typing import Any, List, Optional, cast

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import RedirectResponse
from sqlmodel import Session, select

from app.config import settings
from app.db.session import get_session
from app.models.square_connection import (
    SquareConnection,
    SquareLocation,
    SquareOrder,
    SquarePayment,
)
from app.schemas.square import (
    OAuthUrlResponse,
    SquareConnectionActionResponse,
    SquareConnectionRead,
    SquareLocationRead,
    SquareOrderRead,
    SquarePaymentRead,
    SquareSyncSettingsUpdate,
)
from app.services.square_client import (
    SquareAPIError,
    get_merchant,
    list_locations,
    list_payments,
    retrieve_order,
)
from app.services.square_oauth import (
    build_square_oauth_url,
    exchange_code_for_token,
    revoke_square_token,  # ✅ added
)

router = APIRouter()

JsonDict = dict[str, Any]


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def parse_square_datetime(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def get_str(data: JsonDict, key: str) -> Optional[str]:
    value: object = data.get(key)
    return value if isinstance(value, str) else None


def get_required_str(data: JsonDict, key: str) -> str:
    value: object = data.get(key)
    if not isinstance(value, str) or not value:
        raise HTTPException(
            status_code=400,
            detail=f"Missing required Square field: {key}",
        )
    return value


def get_int(data: JsonDict, key: str) -> Optional[int]:
    value: object = data.get(key)
    return value if isinstance(value, int) else None


def get_dict(data: JsonDict, key: str) -> JsonDict:
    value: object = data.get(key)
    if isinstance(value, dict):
        return cast(JsonDict, value)
    return {}


def get_list_of_dicts(data: JsonDict, key: str) -> list[JsonDict]:
    value: object = data.get(key)
    if not isinstance(value, list):
        return []
    raw_items = cast(list[object], value)
    results: list[JsonDict] = []
    for item in raw_items:
        item_value: object = item
        if isinstance(item_value, dict):
            results.append(cast(JsonDict, item_value))
    return results


def get_connection_or_404(session: Session, merchant_id: str) -> SquareConnection:
    statement = select(SquareConnection).where(
        SquareConnection.merchant_id == merchant_id
    )
    connection = session.exec(statement).first()
    if not connection:
        raise HTTPException(
            status_code=404,
            detail=f"Square connection not found for merchant_id={merchant_id}",
        )
    return connection


def upsert_square_connection(
    session: Session,
    token_json: JsonDict,
    merchant_json: JsonDict,
) -> SquareConnection:
    merchant_id = get_required_str(token_json, "merchant_id")
    access_token = get_required_str(token_json, "access_token")

    merchant = get_dict(merchant_json, "merchant")

    statement = select(SquareConnection).where(
        SquareConnection.merchant_id == merchant_id
    )
    connection = session.exec(statement).first()

    now = utc_now()

    if not connection:
        connection = SquareConnection(
            merchant_id=merchant_id,
            access_token=access_token,
            environment=settings.SQUARE_ENVIRONMENT,
            created_at=now,
        )

    connection.connection_status = "connected"
    connection.deleted_at = None
    connection.disconnected_at = None
    connection.token_revoked_at = None
    connection.auto_sync_enabled = True
    connection.connected_at = now

    connection.access_token = access_token
    connection.refresh_token = get_str(token_json, "refresh_token")
    connection.token_type = get_str(token_json, "token_type")
    connection.scope = get_str(token_json, "scope")
    connection.expires_at = parse_square_datetime(get_str(token_json, "expires_at"))

    connection.merchant_name = get_str(merchant, "business_name")
    connection.country = get_str(merchant, "country")
    connection.language_code = get_str(merchant, "language_code")
    connection.status = get_str(merchant, "status")

    connection.raw_token_json = token_json
    connection.raw_merchant_json = merchant_json
    connection.updated_at = now

    session.add(connection)
    session.commit()
    session.refresh(connection)

    return connection


def upsert_square_location(
    session: Session,
    merchant_id: str,
    location_json: JsonDict,
    main_location_id: Optional[str],
) -> SquareLocation:
    location_id = get_required_str(location_json, "id")

    statement = select(SquareLocation).where(
        SquareLocation.merchant_id == merchant_id,
        SquareLocation.location_id == location_id,
    )
    location = session.exec(statement).first()

    now = utc_now()

    if not location:
        location = SquareLocation(
            merchant_id=merchant_id,
            location_id=location_id,
            created_at=now,
            updated_at=now,
        )

    location.name = get_str(location_json, "name")
    location.business_name = get_str(location_json, "business_name")
    location.country = get_str(location_json, "country")
    location.currency = get_str(location_json, "currency")
    location.timezone = get_str(location_json, "timezone")
    location.status = get_str(location_json, "status")
    location.is_main_location = location_id == main_location_id
    location.raw_json = location_json
    location.updated_at = now

    session.add(location)
    session.commit()
    session.refresh(location)

    return location


def upsert_square_payment(
    session: Session,
    merchant_id: str,
    selected_location_id: str,
    payment_json: JsonDict,
) -> SquarePayment:
    payment_id = get_required_str(payment_json, "id")
    amount_money = get_dict(payment_json, "amount_money")

    statement = select(SquarePayment).where(
        SquarePayment.merchant_id == merchant_id,
        SquarePayment.payment_id == payment_id,
    )
    payment = session.exec(statement).first()

    now = utc_now()

    if not payment:
        payment = SquarePayment(
            merchant_id=merchant_id,
            payment_id=payment_id,
            created_at=now,
            updated_at=now,
        )

    payment.location_id = get_str(payment_json, "location_id") or selected_location_id
    payment.order_id = get_str(payment_json, "order_id")
    payment.status = get_str(payment_json, "status")
    payment.source_type = get_str(payment_json, "source_type")
    payment.amount = get_int(amount_money, "amount")
    payment.currency = get_str(amount_money, "currency")
    payment.created_at_square = parse_square_datetime(get_str(payment_json, "created_at"))
    payment.updated_at_square = parse_square_datetime(get_str(payment_json, "updated_at"))
    payment.raw_json = payment_json
    payment.updated_at = now

    session.add(payment)
    session.commit()
    session.refresh(payment)

    return payment


def upsert_square_order(
    session: Session,
    merchant_id: str,
    order_json: JsonDict,
) -> SquareOrder:
    order_id = get_required_str(order_json, "id")
    total_money = get_dict(order_json, "total_money")

    statement = select(SquareOrder).where(
        SquareOrder.merchant_id == merchant_id,
        SquareOrder.order_id == order_id,
    )
    order = session.exec(statement).first()

    now = utc_now()

    if not order:
        order = SquareOrder(
            merchant_id=merchant_id,
            order_id=order_id,
            created_at=now,
            updated_at=now,
        )

    order.location_id = get_str(order_json, "location_id")
    order.state = get_str(order_json, "state")
    order.total_amount = get_int(total_money, "amount")
    order.currency = get_str(total_money, "currency")
    order.created_at_square = parse_square_datetime(get_str(order_json, "created_at"))
    order.updated_at_square = parse_square_datetime(get_str(order_json, "updated_at"))
    order.raw_json = order_json
    order.updated_at = now

    session.add(order)
    session.commit()
    session.refresh(order)

    return order


# ── Routes ────────────────────────────────────────────────────────────────────

@router.get("/oauth/url", response_model=OAuthUrlResponse)
def get_square_oauth_url() -> OAuthUrlResponse:
    auth_url, state = build_square_oauth_url()
    return OAuthUrlResponse(auth_url=auth_url, state=state)


@router.get("/oauth/callback")
def square_oauth_callback(
    code: Optional[str] = None,
    state: Optional[str] = None,
    error: Optional[str] = None,
    error_description: Optional[str] = None,
    session: Session = Depends(get_session),
) -> RedirectResponse:
    # ✅ if user clicks Deny, redirect back to /account/connect
    if error:
        return RedirectResponse(
            url=f"{settings.FRONTEND_URL}/account/connect?error={error}",
            status_code=302,
        )
    if not code:
        raise HTTPException(status_code=400, detail="Missing OAuth code")
    if not state:
        raise HTTPException(status_code=400, detail="Missing OAuth state")

    try:
        token_json = exchange_code_for_token(code)
        merchant_id = get_required_str(token_json, "merchant_id")
        access_token = get_required_str(token_json, "access_token")
        merchant_json = get_merchant(
            access_token=access_token,
            merchant_id=merchant_id,
        )
        upsert_square_connection(
            session=session,
            token_json=token_json,
            merchant_json=merchant_json,
        )
    except SquareAPIError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc

    return RedirectResponse(
        url=f"{settings.FRONTEND_URL}/account/connect/callback",
        status_code=302,
    )


@router.get("/connections", response_model=List[SquareConnectionRead])
def get_square_connections(
    session: Session = Depends(get_session),
) -> List[SquareConnectionRead]:
    connections = session.exec(select(SquareConnection)).all()
    return cast(List[SquareConnectionRead], connections)


@router.get("/merchant/{merchant_id}")
def get_square_merchant(
    merchant_id: str,
    session: Session = Depends(get_session),
) -> JsonDict:
    connection = get_connection_or_404(session, merchant_id)

    try:
        merchant_json = get_merchant(
            access_token=connection.access_token,
            merchant_id=merchant_id,
        )
    except SquareAPIError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc

    merchant = get_dict(merchant_json, "merchant")

    connection.raw_merchant_json = merchant_json
    connection.updated_at = utc_now()
    connection.merchant_name = get_str(merchant, "business_name")
    connection.country = get_str(merchant, "country")
    connection.language_code = get_str(merchant, "language_code")
    connection.status = get_str(merchant, "status")

    session.add(connection)
    session.commit()
    session.refresh(connection)

    return {"merchant_id": merchant_id, "merchant": merchant_json}


@router.get("/locations/{merchant_id}")
def get_square_locations(
    merchant_id: str,
    session: Session = Depends(get_session),
) -> JsonDict:
    connection = get_connection_or_404(session, merchant_id)

    try:
        locations_json = list_locations(access_token=connection.access_token)
    except SquareAPIError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc

    merchant_raw: JsonDict = connection.raw_merchant_json or {}
    merchant = get_dict(merchant_raw, "merchant")
    main_location_id = get_str(merchant, "main_location_id")

    saved_locations: list[SquareLocation] = []

    for location_json in get_list_of_dicts(locations_json, "locations"):
        saved_location = upsert_square_location(
            session=session,
            merchant_id=merchant_id,
            location_json=location_json,
            main_location_id=main_location_id,
        )
        saved_locations.append(saved_location)

    return {
        "merchant_id": merchant_id,
        "count": len(saved_locations),
        "locations": [
            SquareLocationRead.model_validate(loc).model_dump(mode="json")
            for loc in saved_locations
        ],
        "raw": locations_json,
    }


@router.get("/payments/{merchant_id}")
def get_square_payments(
    merchant_id: str,
    location_id: str = Query(..., description="Square location_id selected by user"),
    begin_time: Optional[str] = Query(default=None, description="Optional RFC3339 begin time"),
    end_time: Optional[str] = Query(default=None, description="Optional RFC3339 end time"),
    limit: int = Query(default=100, ge=1, le=100),
    cursor: Optional[str] = Query(default=None),
    session: Session = Depends(get_session),
) -> JsonDict:
    connection = get_connection_or_404(session, merchant_id)

    try:
        payments_json = list_payments(
            access_token=connection.access_token,
            location_id=location_id,
            begin_time=begin_time,
            end_time=end_time,
            limit=limit,
            cursor=cursor,
        )
    except SquareAPIError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc

    saved_payments: list[SquarePayment] = []

    for payment_json in get_list_of_dicts(payments_json, "payments"):
        saved_payment = upsert_square_payment(
            session=session,
            merchant_id=merchant_id,
            selected_location_id=location_id,
            payment_json=payment_json,
        )
        saved_payments.append(saved_payment)

    return {
        "merchant_id": merchant_id,
        "location_id": location_id,
        "count": len(saved_payments),
        "cursor": get_str(payments_json, "cursor"),
        "payments": [
            SquarePaymentRead.model_validate(p).model_dump(mode="json")
            for p in saved_payments
        ],
        "raw": payments_json,
    }


@router.get("/orders/{merchant_id}/{order_id}")
def get_square_order(
    merchant_id: str,
    order_id: str,
    session: Session = Depends(get_session),
) -> JsonDict:
    connection = get_connection_or_404(session, merchant_id)

    try:
        order_json_response = retrieve_order(
            access_token=connection.access_token,
            order_id=order_id,
        )
    except SquareAPIError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc

    order_json = get_dict(order_json_response, "order")

    if not order_json:
        raise HTTPException(
            status_code=404,
            detail="Square order response did not include order",
        )

    saved_order = upsert_square_order(
        session=session,
        merchant_id=merchant_id,
        order_json=order_json,
    )

    return {
        "merchant_id": merchant_id,
        "order_id": order_id,
        "order": SquareOrderRead.model_validate(saved_order).model_dump(mode="json"),
        "raw": order_json_response,
    }


@router.patch(
    "/connections/{merchant_id}/sync-settings",
    response_model=SquareConnectionActionResponse,
)
def update_sync_settings(
    merchant_id: str,
    payload: SquareSyncSettingsUpdate,
    session: Session = Depends(get_session),
) -> SquareConnection:
    connection = get_connection_or_404(session, merchant_id)

    if connection.connection_status == "deleted":
        raise HTTPException(status_code=400, detail="Connection deleted")

    connection.auto_sync_enabled = payload.auto_sync_enabled

    session.add(connection)
    session.commit()
    session.refresh(connection)

    return connection


@router.post(
    "/connections/{merchant_id}/disconnect",
    response_model=SquareConnectionActionResponse,
)
def disconnect_connection(
    merchant_id: str,
    session: Session = Depends(get_session),
) -> SquareConnection:
    connection = get_connection_or_404(session, merchant_id)

    if connection.connection_status == "deleted":
        raise HTTPException(status_code=400, detail="Already deleted")

    now = utc_now()

    # ✅ revoke token with Square before clearing locally
    if connection.access_token:
        revoke_square_token(connection.access_token)

    connection.connection_status = "disconnected"
    connection.auto_sync_enabled = False
    connection.disconnected_at = now
    connection.access_token = ""
    connection.refresh_token = None
    connection.token_revoked_at = now
    connection.raw_token_json = {}
    connection.updated_at = now

    session.add(connection)
    session.commit()
    session.refresh(connection)

    return connection


@router.delete(
    "/connections/{merchant_id}",
    response_model=SquareConnectionActionResponse,
)
def delete_connection(
    merchant_id: str,
    session: Session = Depends(get_session),
) -> SquareConnection:
    connection = get_connection_or_404(session, merchant_id)

    now = utc_now()

    # ✅ revoke token with Square before clearing locally
    if connection.access_token:
        revoke_square_token(connection.access_token)

    connection.connection_status = "deleted"
    connection.auto_sync_enabled = False
    connection.deleted_at = now
    connection.access_token = ""
    connection.refresh_token = None
    connection.token_revoked_at = now
    connection.raw_token_json = {}
    connection.updated_at = now

    session.add(connection)
    session.commit()
    session.refresh(connection)

    return connection