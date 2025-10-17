import asyncio
import logging
import time
from collections.abc import Mapping
from dataclasses import dataclass
from enum import Enum
from typing import final, override
from uuid import UUID

from httpx import AsyncClient, Client, Request, Response
from pydantic import TypeAdapter
from pydantic.types import JsonValue

from ..models import QECExperiment
from .request import ApiRequest, HttpxClient

logger = logging.getLogger(__name__)


class State(str, Enum):
    SCHEDULED = "Scheduled"
    """The experiment is scheduled and waiting to be picked up by a worker."""
    PENDING = "Pending"
    """The experiment is pending and waiting for resources to be available."""
    RUNNING = "Running"
    """The experiment is currently running."""
    PAUSED = "Paused"
    """The experiment is paused. (e.g. the server is under maintenance)"""
    CANCELLING = "Cancelling"
    """The experiment is being cancelled."""
    CANCELLED = "Cancelled"
    """The experiment was cancelled."""
    COMPLETED = "Completed"
    """The experiment completed successfully."""
    FAILED = "Failed"
    """The experiment failed due to an error."""


@dataclass
class ExperimentStatus:
    run_id: UUID
    state: State
    """The current state of the experiment run."""
    final: bool
    """Whether the experiment run is in a final state."""
    experiment: Mapping[str, JsonValue]
    """The experiment parameters."""
    reason: str | None = None
    """The reason for failure, if any."""

    def raise_for_failure(self) -> None:
        """
        Raise an exception if the run is in a cancelling, cancelled or failure states.

        Args:
            state: Current state of the run
            run_id: UUID of the experiment run
            start_time: Time when the run started (extra context for timeout error reporting)

        Raises:
            RuntimeError: If the run is in a failure state
        """

        run_id = self.run_id
        state = self.state
        failed_reason = self.reason

        match state:
            case State.CANCELLING:
                raise RuntimeError(f"Experiment run '{run_id}' is being cancelled")
            case State.CANCELLED:
                raise RuntimeError(f"Experiment run '{run_id}' was cancelled")
            case State.FAILED:
                if isinstance(failed_reason, str):
                    raise RuntimeError(
                        f"Experiment run '{run_id}' failed: {failed_reason}"
                    )

                raise RuntimeError(
                    f"Experiment run '{run_id}' failed due an internal error"
                )
            case (
                State.SCHEDULED
                | State.PENDING
                | State.RUNNING
                | State.PAUSED
                | State.COMPLETED
            ):
                return


type ExperimentResult = dict[str, JsonValue]


@final
class SubmitExperiment(ApiRequest[UUID]):
    def __init__(self, experiment: QECExperiment):
        self.experiment = experiment

    @override
    def build(self, client: HttpxClient) -> Request:
        return client.build_request(
            method="POST", url="/experiment_run/", json=self.experiment.model_dump()
        )

    @override
    def parse_response(self, response: Response) -> UUID:
        @dataclass
        class RunSubmitResponse:
            run_id: UUID

        result = TypeAdapter(RunSubmitResponse).validate_python(response.json())
        return result.run_id


@final
class GetExperimentStatus(ApiRequest[ExperimentStatus]):
    """Get an experiment run status by its ID."""

    def __init__(self, run_id: UUID):
        self.run_id = run_id

    @override
    def build(self, client: HttpxClient) -> Request:
        return client.build_request(method="GET", url=f"/experiment_run/{self.run_id}")

    @override
    def parse_response(self, response: Response) -> ExperimentStatus:
        # Add run_id to the response data
        data = {
            "run_id": self.run_id,
            **response.json(),
        }
        return TypeAdapter(ExperimentStatus).validate_python(data)

    def send_wait_until_completed(
        self,
        client: Client,
        *,
        timeout: int | None = None,
        interval: float = 1.0,
        raise_on_failure_state: bool = True,
    ) -> ExperimentStatus:
        """Poll the experiment run status until it is completed."""

        self.__check_interval_timeout(interval=interval, timeout=timeout)

        start_time = time.time()

        while True:
            # Get the current status
            status = self.send(client)
            logger.debug(f"Experiment run '{self.run_id}' current status: {status}")

            # Raise for failure state
            if raise_on_failure_state:
                status.raise_for_failure()

            # Raise for user provided timeout
            if timeout is not None:
                _raise_for_timeout(start_time, timeout)

            # Check if the run is completed
            if status.state == State.COMPLETED:
                # Get and return the status
                return status

            # Wait
            time.sleep(interval)

    async def send_wait_until_completed_async(
        self,
        client: AsyncClient,
        *,
        timeout: int | None = None,
        interval: float = 1.0,
        raise_on_failure_state: bool = True,
    ) -> ExperimentStatus:
        """Poll the experiment run status until it is completed."""

        self.__check_interval_timeout(interval=interval, timeout=timeout)

        start_time = time.time()

        while True:
            # Get the current status
            status = await self.send_async(client)

            status = self.__check_final_state(
                status=status,
                start_time=start_time,
                timeout=timeout,
                raise_on_failure_state=raise_on_failure_state,
            )

            # Return if final
            if status is not None:
                return status

            # Wait
            await asyncio.sleep(interval)

    def __check_interval_timeout(
        self,
        *,
        interval: float,
        timeout: int | None,
    ) -> None:
        """Sanity check for interval and timeout values."""

        if interval < 1.0:
            raise ValueError("The minimum `interval` is 1.0 second")

        if timeout is not None:
            if timeout <= 0:
                raise ValueError("The `timeout` must be greater than 0")

            if interval > timeout:
                raise ValueError(
                    "The `interval` cannot be greater than the given `timeout`"
                )

    def __check_final_state(
        self,
        *,
        status: ExperimentStatus,
        start_time: float,
        timeout: int | None,
        raise_on_failure_state: bool,
    ) -> ExperimentStatus | None:
        logger.debug(f"Experiment run '{self.run_id}' current status: {status.state}")

        # Check if the run is completed
        if status.state == State.COMPLETED:
            # Get and return the status
            return status

        # Raise for failure state
        if raise_on_failure_state:
            status.raise_for_failure()

        # Check if final status
        if status.final:
            return status

        # Raise for user provided timeout
        if timeout is not None:
            _raise_for_timeout(start_time, timeout)

        # Still pending
        return None


@final
class GetExperimentResult(ApiRequest[ExperimentResult]):
    def __init__(self, run_id: UUID):
        self.run_id = run_id

    @override
    def build(self, client: HttpxClient) -> Request:
        return client.build_request(
            method="GET", url=f"/experiment_run/{self.run_id}/result"
        )

    @override
    def parse_response(self, response: Response) -> ExperimentResult:
        return TypeAdapter(dict[str, JsonValue]).validate_python(response.json())


def _raise_for_timeout(start_time: float, timeout: int):
    """
    Raise a `TimeoutError` if `timeout` seconds have passed since `start_time`.
    """
    import time

    if (time.time() - start_time) > timeout:
        raise TimeoutError(f"The request timed out after {timeout} seconds")
