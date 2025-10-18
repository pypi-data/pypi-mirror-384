from httpx import Client
from httpx._types import QueryParamTypes


class ProviderClient:

    def __init__(self, client):
        self._client: Client = client

    def create(self, platform: str, data: dict) -> dict:
        data.update({
            'provider': platform,
        })

        res = self._client.post(
            url='/v1/provider/',
            json=data,
        )

        return res.json()

    def list(self, params: QueryParamTypes = None) -> dict:
        res = self._client.get(
            url='/v1/provider/',
            params=params,
        )

        return res.json()

    def get(self, uuid: str) -> dict:
        res = self._client.get(
            url=f'/v1/provider/{uuid}/',
        )

        return res.json()

    def update(self, uuid: str, data: dict, file = None) -> dict:
        files = {
            'profile_picture':file,
        }

        res = self._client.patch(
            url=f'/v1/provider/{uuid}/',
            json=data,
            files=files,
        )

        return res.json()

    def delete(self, uuid: str) -> dict:
        res = self._client.delete(
            url=f'/v1/provider/{uuid}',
        )

        return res.json()
