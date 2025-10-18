from httpx import Client

from radex_booking.clients import ClientBase, ProviderClient, ResourceClient, CustomerClient, BookingClient


class Booking:

    def __init__(self, base_url: str = None, key: str = None, client: Client = None):
        self.base_url = base_url
        self.key = key

        self._client = client or ClientBase(
            base_url=base_url,
            headers={
                'Authorization': f'Bearer {key}'
            },
        )

        self.provider = ProviderClient(client)
        self.resource = ResourceClient(client)
        self.customer = CustomerClient(client)
        self.booking = BookingClient(client)
