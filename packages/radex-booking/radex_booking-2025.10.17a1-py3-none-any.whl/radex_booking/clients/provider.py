from httpx._types import QueryParamTypes

from radex_booking.clients import ClientBase


class ProviderClient(ClientBase):

    def create(self, platform: str, data: dict) -> dict:
        data.update({
            'platform': platform,
        })

        res = self._make_request(
            method='POST',
            url='/v1/provider/',
            json=data,
        )

        return res.json()

    def list(self, params: QueryParamTypes = None) -> dict:
        res = self._make_request(
            method='GET',
            url='/v1/provider/',
            params=params,
        )

        return res.json()

    def get(self, uuid: str) -> dict:
        res = self._make_request(
            method='GET',
            url=f'/v1/provider/{uuid}/',
        )

        return res.json()

    def update(self, uuid: str, data: dict) -> dict:
        res = self._make_request(
            method='PATCH',
            url=f'/v1/provider/{uuid}/',
            json=data,
        )

        return res.json()

    #  todo  update profile picture

    def delete(self, uuid: str) -> dict:
        res = self._make_request(
            method='DELETE',
            url=f'/v1/provider/{uuid}/',
        )

        return res.json()
