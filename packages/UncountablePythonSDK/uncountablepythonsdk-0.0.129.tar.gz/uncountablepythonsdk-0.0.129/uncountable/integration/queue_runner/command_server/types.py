import asyncio
import typing
from dataclasses import dataclass
from enum import StrEnum

from uncountable.types import queued_job_t


class CommandType(StrEnum):
    ENQUEUE_JOB = "enqueue_job"
    RETRY_JOB = "retry_job"
    VACCUUM_QUEUED_JOBS = "vaccuum_queued_jobs"


RT = typing.TypeVar("RT")


@dataclass(kw_only=True)
class CommandBase[RT]:
    type: CommandType
    response_queue: asyncio.Queue[RT]


@dataclass(kw_only=True)
class CommandEnqueueJobResponse:
    queued_job_uuid: str


@dataclass(kw_only=True)
class CommandRetryJobResponse:
    queued_job_uuid: str | None


@dataclass(kw_only=True)
class CommandVaccuumQueuedJobsResponse:
    pass


@dataclass(kw_only=True)
class CommandEnqueueJob(CommandBase[CommandEnqueueJobResponse]):
    type: CommandType = CommandType.ENQUEUE_JOB
    job_ref_name: str
    payload: queued_job_t.QueuedJobPayload
    response_queue: asyncio.Queue[CommandEnqueueJobResponse]


@dataclass(kw_only=True)
class CommandRetryJob(CommandBase[CommandRetryJobResponse]):
    type: CommandType = CommandType.RETRY_JOB
    queued_job_uuid: str


@dataclass(kw_only=True)
class CommandVaccuumQueuedJobs(CommandBase[CommandVaccuumQueuedJobsResponse]):
    type: CommandType = CommandType.VACCUUM_QUEUED_JOBS


_Command = CommandEnqueueJob | CommandRetryJob | CommandVaccuumQueuedJobs


CommandQueue = asyncio.Queue[_Command]

CommandTask = asyncio.Task[_Command]


class CommandServerException(Exception):
    pass


class CommandServerTimeout(CommandServerException):
    pass


class CommandServerBadResponse(CommandServerException):
    pass
