import asyncio

import grpc.aio as grpc_aio
import simplejson as json
from google.protobuf.timestamp_pb2 import Timestamp
from grpc import StatusCode

from pkgs.argument_parser import CachedParser
from uncountable.core.environment import get_local_admin_server_port
from uncountable.integration.queue_runner.command_server.protocol.command_server_pb2 import (
    CheckHealthRequest,
    CheckHealthResult,
    EnqueueJobRequest,
    EnqueueJobResult,
    ListQueuedJobsRequest,
    ListQueuedJobsResult,
    RetryJobRequest,
    RetryJobResult,
    VaccuumQueuedJobsRequest,
    VaccuumQueuedJobsResult,
)
from uncountable.integration.queue_runner.command_server.types import (
    CommandEnqueueJob,
    CommandEnqueueJobResponse,
    CommandQueue,
    CommandRetryJob,
    CommandRetryJobResponse,
    CommandVaccuumQueuedJobs,
    CommandVaccuumQueuedJobsResponse,
)
from uncountable.integration.queue_runner.datastore import DatastoreSqlite
from uncountable.types import queued_job_t

from .constants import ListQueuedJobsConstants
from .protocol.command_server_pb2_grpc import (
    CommandServerServicer,
    add_CommandServerServicer_to_server,
)

queued_job_payload_parser = CachedParser(queued_job_t.QueuedJobPayload)


async def serve(command_queue: CommandQueue, datastore: DatastoreSqlite) -> None:
    server = grpc_aio.server()

    class CommandServerHandler(CommandServerServicer):
        async def EnqueueJob(
            self, request: EnqueueJobRequest, context: grpc_aio.ServicerContext
        ) -> EnqueueJobResult:
            payload_json = json.loads(request.serialized_payload)
            payload = queued_job_payload_parser.parse_api(payload_json)
            response_queue: asyncio.Queue[CommandEnqueueJobResponse] = asyncio.Queue()
            await command_queue.put(
                CommandEnqueueJob(
                    job_ref_name=request.job_ref_name,
                    payload=payload,
                    response_queue=response_queue,
                )
            )
            response = await response_queue.get()
            result = EnqueueJobResult(
                successfully_queued=True, queued_job_uuid=response.queued_job_uuid
            )
            return result

        async def RetryJob(
            self, request: RetryJobRequest, context: grpc_aio.ServicerContext
        ) -> RetryJobResult:
            response_queue: asyncio.Queue[CommandRetryJobResponse] = asyncio.Queue()
            await command_queue.put(
                CommandRetryJob(
                    queued_job_uuid=request.uuid, response_queue=response_queue
                )
            )
            response = await response_queue.get()
            if response.queued_job_uuid is not None:
                return RetryJobResult(
                    successfully_queued=True, queued_job_uuid=response.queued_job_uuid
                )
            else:
                return RetryJobResult(successfully_queued=False, queued_job_uuid="")

        async def CheckHealth(
            self, request: CheckHealthRequest, context: grpc_aio.ServicerContext
        ) -> CheckHealthResult:
            return CheckHealthResult(success=True)

        async def ListQueuedJobs(
            self, request: ListQueuedJobsRequest, context: grpc_aio.ServicerContext
        ) -> ListQueuedJobsResult:
            if (
                request.limit < ListQueuedJobsConstants.LIMIT_MIN
                or request.limit > ListQueuedJobsConstants.LIMIT_MAX
            ):
                await context.abort(
                    StatusCode.INVALID_ARGUMENT, "Limit must be between 1 and 100."
                )

            if request.offset < ListQueuedJobsConstants.OFFSET_MIN:
                await context.abort(
                    StatusCode.INVALID_ARGUMENT, "Offset cannot be negative."
                )

            queued_job_metadata = datastore.list_queued_job_metadata(
                offset=request.offset, limit=request.limit
            )

            response_list: list[ListQueuedJobsResult.ListQueuedJobsResultItem] = []
            for item in queued_job_metadata:
                proto_timestamp = Timestamp()
                proto_timestamp.FromDatetime(item.submitted_at)

                response_list.append(
                    ListQueuedJobsResult.ListQueuedJobsResultItem(
                        uuid=item.queued_job_uuid,
                        job_ref_name=item.job_ref_name,
                        num_attempts=item.num_attempts,
                        submitted_at=proto_timestamp,
                        status=item.status,
                    )
                )
            return ListQueuedJobsResult(queued_jobs=response_list)

        async def VaccuumQueuedJobs(
            self, request: VaccuumQueuedJobsRequest, context: grpc_aio.ServicerContext
        ) -> VaccuumQueuedJobsResult:
            response_queue: asyncio.Queue[CommandVaccuumQueuedJobsResponse] = (
                asyncio.Queue()
            )
            await command_queue.put(
                CommandVaccuumQueuedJobs(response_queue=response_queue)
            )
            return VaccuumQueuedJobsResult()

    add_CommandServerServicer_to_server(CommandServerHandler(), server)

    listen_addr = f"[::]:{get_local_admin_server_port()}"

    server.add_insecure_port(listen_addr)

    await server.start()
    await server.wait_for_termination()
