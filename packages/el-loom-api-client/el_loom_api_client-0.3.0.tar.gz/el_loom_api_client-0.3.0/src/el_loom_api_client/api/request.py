from abc import ABC, abstractmethod
from typing import Generic, TypeVar

import httpx

from ..api.error import raise_for_error_response

T = TypeVar("T")

type HttpxClient = httpx.Client | httpx.AsyncClient


class ApiRequest(ABC, Generic[T]):
    """Base class for API requests.

    `T` is the type of the parsed result obtained from the response.
    """

    @abstractmethod
    def build(self, client: HttpxClient) -> httpx.Request:
        """
        Builds the HTTP request, returning an `httpx.Request` object.

        The url should be relative to the client's base URL.
        """
        raise NotImplementedError()

    @abstractmethod
    def parse_response(self, response: httpx.Response) -> T:
        """Parses the `httpx.Response` to return a result of type `T`."""
        raise NotImplementedError()

    def send_raw(self, client: httpx.Client) -> httpx.Response:
        """Sends the request and returns the raw `httpx.Response`."""
        request = self.build(client)
        response = client.send(request)
        return raise_for_error_response(response)

    def send(self, client: httpx.Client) -> T:
        """Sends the request and returns the parsed response result."""
        response = self.send_raw(client)
        return self.parse_response(response)

    async def send_raw_async(self, client: httpx.AsyncClient) -> httpx.Response:
        """Sends the request and returns the raw `httpx.Response`."""
        request = self.build(client)
        response = await client.send(request)
        return raise_for_error_response(response)

    async def send_async(self, client: httpx.AsyncClient) -> T:
        """Sends the request and returns the parsed response result."""
        response = await self.send_raw_async(client)
        return self.parse_response(response)
