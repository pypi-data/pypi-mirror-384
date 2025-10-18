from httpx._types import QueryParamTypes

from radex_booking.clients import ClientBase


class BookingClient(ClientBase):

    def create(self, platform: str, resource: str, customer: str, data: dict) -> dict:
        data.update({
            'platform': platform,
            'resource': resource,
            'customer': customer,
        })

        res = self._make_request(
            method='POST',
            url='/v1/booking/',
            json=data,
        )

        return res.json()

    def list(self, params: QueryParamTypes = None) -> dict:
        res = self._make_request(
            method='GET',
            url='/v1/booking/',
            params=params,
        )

        return res.json()

    def get(self, uuid: str) -> dict:
        res = self._make_request(
            method='GET',
            url=f'/v1/booking/{uuid}/',
        )

        return res.json()

    def update(self, uuid: str, data: dict) -> dict:
        res = self._make_request(
            method='PATCH',
            url=f'/v1/booking/{uuid}/',
            json=data,
        )

        return res.json()

    def availability(self, params: QueryParamTypes = None) -> dict:
        res = self._make_request(
            method='GET',
            url='/v1/booking/availability/',
            params=params,
        )

        return res.json()
