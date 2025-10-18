from httpx import Client
from httpx._types import QueryParamTypes


class BookingClient:

    def __init__(self, client):
        self._client: Client = client

    def create(self, platform: str, resource: str, customer: str, data: dict) -> dict:
        data.update({
            'provider': platform,
            'resource': resource,
            'customer': customer,
        })

        res = self._client.post(
            url='/v1/radex_booking/',
            json=data,
        )

        return res.json()

    def list(self, params: QueryParamTypes = None) -> dict:
        res = self._client.get(
            url='/v1/radex_booking/',
            params=params,
        )

        return res.json()

    def get(self, uuid: str) -> dict:
        res = self._client.get(
            url=f'/v1/radex_booking/{uuid}/',
        )

        return res.json()

    def update(self, uuid: str, data: dict) -> dict:
        res = self._client.patch(
            url=f'/v1/radex_booking/{uuid}/',
            json=data,
        )

        return res.json()
