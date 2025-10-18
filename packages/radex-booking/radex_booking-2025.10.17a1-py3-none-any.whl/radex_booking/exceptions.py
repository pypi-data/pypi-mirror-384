import json
import typing

from httpx import Response


class ClientException(Exception):
    code: int

    def __init__(
        self,
        response: Response | None,
        errors: str | None,
    ) -> None:
        self.response = response
        self.errors = errors

    def __str__(self) -> str:
        return f'{self.__class__.__name__}({self.errors})'

    def __repr__(self) -> str:
        return self.__str__()

    @property
    def status_code(self) -> int | None:
        return self.response.status_code if self.response is not None else None

    @classmethod
    def from_response(cls, response: Response):
        try:
            res_content = response.json()
            errors = json.dumps(res_content, indent=2)
        except json.JSONDecodeError as exc:
            errors = response.status_code

        return cls._get_error(response.status_code)(
            response=response,
            errors=errors,
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


class ServerError(ClientException):
    code = 500
