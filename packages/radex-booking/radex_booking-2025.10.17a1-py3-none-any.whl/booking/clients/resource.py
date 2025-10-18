from httpx import Client
from httpx._types import QueryParamTypes


class ResourceClient:

    def __init__(self, client):
        self._client: Client = client

    def create(self, provider: str, data: dict) -> dict:
        data.update({
            'provider': provider,
        })

        res = self._client.post(
            url='/v1/resource/',
            json=data,
        )

        return res.json()

    def list(self, params: QueryParamTypes = None) -> dict:
        res = self._client.get(
            url='/v1/resource/',
            params=params,
        )

        return res.json()

    def get(self, uuid: str) -> dict:
        res = self._client.get(
            url=f'/v1/resource/{uuid}/',
        )

        return res.json()

    def update(self, uuid: str, data: dict) -> dict:
        res = self._client.patch(
            url=f'/v1/resource/{uuid}/',
            json=data,
        )

        return res.json()

    def delete(self, uuid: str) -> dict:
        res = self._client.delete(
            url=f'/v1/resource/{uuid}',
        )

        return res.json()
