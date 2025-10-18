from httpx import Client, Response

from radex_booking.exceptions import ClientException


class ClientBase:

    def __init__(self, client):
        self._client: Client = client

    def _make_request(self, method, url, *args, **kwargs) -> Response:
        res = self._client.request(method=method, url=url, *args, **kwargs)

        if res.status_code >= 400:
            raise ClientException.from_response(res)

        return res


from .provider import ProviderClient
from .resource import ResourceClient
from .customer import CustomerClient
from .booking import BookingClient
