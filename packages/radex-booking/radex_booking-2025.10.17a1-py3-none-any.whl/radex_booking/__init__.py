from httpx import Client

from radex_booking.clients import ProviderClient, ResourceClient, CustomerClient, BookingClient


class RadexBooking:
    CLIENT_ID = 'fbpOneIgVoTIDE4FxAzZMSxlpyCq7myFdh6xITnR'

    def __init__(self, base_url: str = None, key: str = None, client: Client = None):
        self.base_url = base_url
        self.key = key

        self._client = client or Client(
            base_url=base_url,
            headers={
                'Authorization': f'Bearer {key}'
            },
        )
        self._client.headers.update({
            'X-Application': self.CLIENT_ID
        })

        self.provider = ProviderClient(self._client)
        self.resource = ResourceClient(self._client)
        self.customer = CustomerClient(self._client)
        self.booking = BookingClient(self._client)
