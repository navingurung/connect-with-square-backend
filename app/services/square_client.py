from typing import Any, Optional

import requests

from app.config import settings


class SquareAPIError(Exception):
    def __init__(self, status_code: int, detail: Any):
        self.status_code = status_code
        self.detail = detail
        super().__init__(str(detail))


def _square_headers(access_token: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {access_token}",
        "Square-Version": settings.SQUARE_VERSION,
        "Content-Type": "application/json",
    }


def _handle_response(response: requests.Response) -> dict[str, Any]:
    try:
        data = response.json()
    except ValueError:
        data = {"message": response.text}

    if response.status_code >= 400:
        raise SquareAPIError(
            status_code=response.status_code,
            detail=data,
        )

    return data


def square_get(
    path: str,
    access_token: str,
    params: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    url = f"{settings.SQUARE_BASE_URL}{path}"

    cleaned_params = {
        key: value for key, value in (params or {}).items() if value is not None
    }

    try:
        response = requests.get(
            url,
            headers=_square_headers(access_token),
            params=cleaned_params,
            timeout=30,
        )
    except requests.RequestException as exc:
        raise SquareAPIError(
            status_code=500,
            detail={"message": "Square request failed", "error": str(exc)},
        ) from exc

    return _handle_response(response)


def get_merchant(access_token: str, merchant_id: str) -> dict[str, Any]:
    return square_get(
        path=f"/v2/merchants/{merchant_id}",
        access_token=access_token,
    )


def list_locations(access_token: str) -> dict[str, Any]:
    return square_get(
        path="/v2/locations",
        access_token=access_token,
    )


def list_payments(
    access_token: str,
    location_id: str,
    begin_time: Optional[str] = None,
    end_time: Optional[str] = None,
    limit: int = 100,
    cursor: Optional[str] = None,
) -> dict[str, Any]:
    return square_get(
        path="/v2/payments",
        access_token=access_token,
        params={
            "location_id": location_id,
            "begin_time": begin_time,
            "end_time": end_time,
            "limit": limit,
            "cursor": cursor,
        },
    )


def retrieve_order(access_token: str, order_id: str) -> dict[str, Any]:
    return square_get(
        path=f"/v2/orders/{order_id}",
        access_token=access_token,
    )