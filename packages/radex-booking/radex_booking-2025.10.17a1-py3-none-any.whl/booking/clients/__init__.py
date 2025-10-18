import typing

from httpx import Client, Response

from .provider import ProviderClient
from .resource import ResourceClient
from .customer import CustomerClient
from .booking import BookingClient


class ClientBase(Client):

    def request(self, *args, **kwargs) -> Response:
        res = super().request(*args, **kwargs)

        if res.status_code >= 400:
            raise ClientException.from_response(res)

        return res


class ClientException(Exception):
    code = 500

    def __init__(self, response: Response | None):
        self.response = response

    def status_code(self) -> int | None:
        return self.response.status_code if self.response is not None else None

    @classmethod
    def from_response(cls, response: Response):
        return cls._get_error(response.status_code)(
            response=response,
        )

    @staticmethod
    def _get_errors() -> dict[int, typing.Type['ClientException']]:
        return {error.code: error for error in ClientException.__subclasses__()}

    @staticmethod
    def _get_error(code: int) -> typing.Type['ClientException']:
        return ClientException._get_errors().get(code)


class BadRequestError(ClientException):
    code = 400


class NotAuthenticatedError(ClientException):
    code = 401


class PermissionDeniedError(ClientException):
    code = 403


class NotFoundError(ClientException):
    code = 404


class MethodNotAllowedError(ClientException):
    code = 405


class NotAcceptableError(ClientException):
    code = 406
