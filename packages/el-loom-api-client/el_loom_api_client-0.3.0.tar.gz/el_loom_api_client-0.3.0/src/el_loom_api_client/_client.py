import logging
from collections.abc import Generator
from functools import lru_cache
from types import TracebackType
from typing import LiteralString, final, override
from uuid import UUID

import httpx
from pydantic import HttpUrl, SecretStr
from typing_extensions import deprecated

from ._config import Config, print_config_error_help
from .api.experiment import (
    ExperimentResult,
    ExperimentStatus,
    GetExperimentResult,
    GetExperimentStatus,
    SubmitExperiment,
)
from .models import QECExperiment

logger = logging.getLogger(__package__)


@final
class _BearerTokenAuth(httpx.Auth):
    """Custom authentication for httpx"""

    def __init__(self, token: SecretStr):
        self._token = token

    @override
    def auth_flow(
        self, request: httpx.Request
    ) -> Generator[httpx.Request, httpx.Response, None]:
        request.headers["Authorization"] = f"Bearer {self._token.get_secret_value()}"
        yield request


class _BaseClient:
    def __init__(
        self,
        api_url: str | HttpUrl | None = None,
        api_token: str | SecretStr | None = None,
    ):
        if isinstance(api_token, str):
            api_token = SecretStr(api_token)

        if isinstance(api_url, str):
            api_url = HttpUrl(api_url)

        kwargs = {}
        if api_token is not None:
            kwargs["api_token"] = api_token
        if api_url is not None:
            kwargs["api_url"] = api_url

        self._config: Config = Config(**kwargs)  # pyright: ignore[reportUnknownArgumentType]

        if not self._config.api_url or not self._config.api_token:
            print_config_error_help()

            raise ValueError("API URL and token must be set via env or config")


class LoomClient(_BaseClient):
    """Client for interacting with the Loom API.

    Example (context manager):

    ```python
    with LoomClient(...) as client:
        # Create your experiment
        experiment = QECExperiment(...)
        # Submit the experiment
        run_id = client.experiment_run(experiment)
        print(run_id)
    ```

    Example: (no context manager):

    ```python
    client = LoomClient(...)
    # Create your experiment
    experiment = QECExperiment(...)
    # Submit the experiment
    run_id = client.experiment_run(experiment)
    print(run_id)
    # Close the client
    client.close()
    ```
    """

    def __init__(
        self,
        api_url: str | HttpUrl | None = None,
        api_token: str | SecretStr | None = None,
    ):
        super().__init__(api_url=api_url, api_token=api_token)

        # Already checked in the base class
        assert self._config.api_token is not None

        self._client: httpx.Client = httpx.Client(
            base_url=str(self._config.api_url),
            headers={
                "User-Agent": _user_agent(),
            },
            auth=_BearerTokenAuth(self._config.api_token),
        )

    @property
    def is_closed(self) -> bool:
        """
        Check if the client is closed
        """
        return self._client.is_closed

    def __enter__(self: "LoomClient") -> "LoomClient":
        _ = self._client.__enter__()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None = None,
        exc_value: BaseException | None = None,
        traceback: TracebackType | None = None,
    ) -> None:
        self._client.__exit__(exc_type, exc_value, traceback)

    def close(self) -> None:
        """Close the client. Once closed, the client cannot be used again.

        The client is automatically closed when used as a context manager (i.e. `with` statement).
        """

        self._client.close()

    def experiment_run(self, experiment: QECExperiment) -> UUID:
        """
        Submit an experiment run to the Loom API.
        """

        return SubmitExperiment(experiment).send(self._client)

    def get_experiment_run_status(self, run_id: UUID) -> ExperimentStatus:
        """
        Get the status of an experiment run by its run ID.
        """

        return GetExperimentStatus(run_id).send(self._client)

    def get_experiment_run_result(self, run_id: UUID) -> ExperimentResult:
        """
        Get the result of a completed experiment run by its run ID.

        **Hint**: Use the `get_experiment_run_status` method first, to check if the run is completed.
        """

        return GetExperimentResult(run_id).send(self._client)

    def wait_for_experiment_run_result(
        self, run_id: UUID, *, timeout: int | None = None, interval: float = 1.0
    ) -> ExperimentResult:
        """
        Waits for an experiment to complete and retrieves the result.

        If `timeout` is specified, the method will raise a `TimeoutError`
        if the experiment does not complete within the given time. If `timeout`
        is `None`, the method will wait indefinitely, though the server may
        still terminate the request due to its own timeout.

        The given `interval` controls how often the client checks the status of
        the experiment. The default and minimum value is `1.0` second.

        If the experiment finish with a failure type state, an exception is raised.
        """

        _ = GetExperimentStatus(run_id).send_wait_until_completed(
            self._client,
            timeout=timeout,
            interval=interval,
            raise_on_failure_state=True,
        )

        # Get and return the result
        return self.get_experiment_run_result(run_id)

    __get_result_sync_deprecated: LiteralString = "LoomClient.get_result_sync() is deprecated; use LoomClient.wait_for_experiment_run_result() instead"

    @deprecated(__get_result_sync_deprecated)
    def get_result_sync(
        self, run_id: UUID, timeout: int | None = None
    ) -> ExperimentResult:
        """
        Waits for an experiment to complete and retrieves the result.

        **Deprecated**: Use `LoomClient.wait_for_experiment_run_result()` instead."""

        return self.wait_for_experiment_run_result(
            run_id, timeout=timeout, interval=1.0
        )


class AsyncLoomClient(_BaseClient):
    """Async client for interacting with the Loom API.

    Example (context manager):

    ```python
    async with AsyncLoomClient(...) as client:
        # Create your experiment
        experiment = QECExperiment(...)
        # Submit the experiment
        run_id = await client.experiment_run(experiment)
        print(run_id)
    ```

    Example: (no context manager):

    ```python
    client = AsyncLoomClient(...)
    # Create your experiment
    experiment = QECExperiment(...)
    # Submit the experiment
    run_id = await client.experiment_run(experiment)
    print(run_id)
    # Close the client
    await client.aclose()
    ```
    """

    def __init__(
        self,
        api_url: str | HttpUrl | None = None,
        api_token: str | SecretStr | None = None,
    ):
        super().__init__(api_url=api_url, api_token=api_token)

        # Already checked in the base class
        assert self._config.api_token is not None

        self._client: httpx.AsyncClient = httpx.AsyncClient(
            base_url=str(self._config.api_url),
            headers={
                "User-Agent": _user_agent(),
            },
            auth=_BearerTokenAuth(self._config.api_token),
        )

    async def __aenter__(self: "AsyncLoomClient") -> "AsyncLoomClient":
        _ = await self._client.__aenter__()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None = None,
        exc_value: BaseException | None = None,
        traceback: TracebackType | None = None,
    ) -> None:
        await self._client.__aexit__(exc_type, exc_value, traceback)

    def __enter__(self):
        raise TypeError("Use 'async with AsyncLoomClient(...)'")

    def __exit__(self, *args):  # pyright: ignore[reportUnknownParameterType, reportMissingParameterType]
        raise TypeError("Use 'async with AsyncLoomClient(...)'")

    async def aclose(self) -> None:
        """Asynchronously close the client. Once closed, the client cannot be used again.

        The client is automatically closed when used as a context manager (i.e. `async with` statement).
        """

        await self._client.aclose()

    async def experiment_run(self, experiment: QECExperiment) -> UUID:
        """
        Submit an experiment run to the Loom API.
        """

        return await SubmitExperiment(experiment).send_async(self._client)

    async def get_experiment_run_status(self, run_id: UUID) -> ExperimentStatus:
        """
        Get the status of an experiment run by its run ID.
        """

        return await GetExperimentStatus(run_id).send_async(self._client)

    async def get_experiment_run_result(self, run_id: UUID) -> ExperimentResult:
        """
        Get the result of a completed experiment run by its run ID.

        **Hint**: Use the `get_experiment_run_status` method first, to check if the run is completed.
        """

        return await GetExperimentResult(run_id).send_async(self._client)

    async def wait_for_experiment_run_result(
        self, run_id: UUID, *, timeout: int | None = None, interval: float = 1.0
    ) -> ExperimentResult:
        """
        Waits for an experiment to complete and retrieves the result.

        If `timeout` is specified, the method will raise a `TimeoutError`
        if the experiment does not complete within the given time. If `timeout`
        is `None`, the method will wait indefinitely, though the server may
        still terminate the request due to its own timeout.

        The given `interval` controls how often the client checks the status of
        the experiment. The default and minimum value is `1.0` second.

        If the experiment finish with a failure type state, an exception is raised.
        """

        _ = await GetExperimentStatus(run_id).send_wait_until_completed_async(
            self._client,
            timeout=timeout,
            interval=interval,
            raise_on_failure_state=True,
        )

        # Get and return the result
        return await self.get_experiment_run_result(run_id)


@lru_cache()
def _user_agent() -> str:
    """User-Agent string for the client."""

    import platform
    from importlib.metadata import metadata, version

    ua: list[str] = []

    # Example: el-loom-api-client/0.2.0 python-httpx/0.28.1 Python/3.13.7 (Darwin; arm64)

    if __package__:
        name = metadata(__package__)["Name"]
        ua += [f"{name}/{version(__package__)}"]

    # httpx
    ua += [f"python-httpx/{httpx.__version__}"]

    # python
    ua += [f"Python/{platform.python_version()}"]

    # Comment: OS, machine
    ua += [f"({platform.system()}; {platform.machine()})"]

    return " ".join(ua)
