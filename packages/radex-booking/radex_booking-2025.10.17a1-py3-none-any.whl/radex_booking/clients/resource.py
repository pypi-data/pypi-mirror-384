from httpx._types import QueryParamTypes

from radex_booking.clients import ClientBase


class ResourceClient(ClientBase):

    def create(self, provider: str, data: dict) -> dict:
        data.update({
            'provider': provider,
        })

        res = self._make_request(
            method='POST',
            url='/v1/resource/',
            json=data,
        )

        return res.json()

    def list(self, params: QueryParamTypes = None) -> dict:
        res = self._make_request(
            method='GET',
            url='/v1/resource/',
            params=params,
        )

        return res.json()

    def get(self, uuid: str) -> dict:
        res = self._make_request(
            method='GET',
            url=f'/v1/resource/{uuid}/',
        )

        return res.json()

    def update(self, uuid: str, data: dict) -> dict:
        res = self._make_request(
            method='PATCH',
            url=f'/v1/resource/{uuid}/',
            json=data,
        )

        return res.json()

    def delete(self, uuid: str) -> dict:
        res = self._make_request(
            method='DELETE',
            url=f'/v1/resource/{uuid}/',
        )

        return res.json()
