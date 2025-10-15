import json
import time
from dataclasses import dataclass
from decimal import Decimal

from uncountable.integration.job import JobArguments, WebhookJob, register_job
from uncountable.types import (
    base_t,
    identifier_t,
    job_definition_t,
    sockets_t,
)
from uncountable.types.integration_session_t import IntegrationSessionInstrument
from websockets.sync.client import connect
from websockets.typing import Data

from pkgs.argument_parser.argument_parser import CachedParser
from pkgs.serialization_util import serialize_for_api


@dataclass(kw_only=True)
class InstrumentPayload:
    equipment_id: base_t.ObjectId


@register_job
class InstrumentExample(WebhookJob[InstrumentPayload]):
    def run(
        self, args: JobArguments, payload: InstrumentPayload
    ) -> job_definition_t.JobResult:
        parser: CachedParser[sockets_t.SocketResponse] = CachedParser(
            sockets_t.SocketResponse  # type:ignore[arg-type]
        )

        def parse_message(message: Data) -> sockets_t.SocketEventData | None:
            try:
                return parser.parse_api(json.loads(message)).data
            except ValueError:
                return None

        integration_session = IntegrationSessionInstrument(
            equipment_key=identifier_t.IdentifierKeyId(id=payload.equipment_id)
        )
        registration_info = args.client.register_sockets_token(
            socket_request=sockets_t.SocketRequestIntegrationSession(
                integration_session=integration_session
            )
        ).response
        token = registration_info.token
        room_key = registration_info.room_key
        args.logger.log_info(f"Token: {token}")

        with connect(
            "ws://host.docker.internal:8765",
            additional_headers={
                "Authorization": f"Bearer {token}",
                "X-UNC-EXTERNAL": "true",
            },
        ) as ws:
            ws.send(
                json.dumps(
                    serialize_for_api(
                        sockets_t.JoinRoomWithTokenSocketClientMessage(token=token)
                    )
                )
            )
            for i in range(10):
                args.logger.log_info("Sending reading...")
                ws.send(
                    json.dumps(
                        serialize_for_api(
                            sockets_t.SendInstrumentReadingClientMessage(
                                value=Decimal(i * 100), room_key=room_key
                            )
                        )
                    )
                )
                time.sleep(0.75)

            while True:
                message = parse_message(ws.recv())
                match message:
                    case sockets_t.UsersInRoomUpdatedEventData():
                        num_users = len(message.user_ids)
                        if num_users <= 1:
                            break
                        else:
                            args.logger.log_info(
                                f"Session still open, {num_users} users in room."
                            )
                    case _:
                        args.logger.log_info("Session still open...")
                        continue

        args.logger.log_info("Session closed.")
        return job_definition_t.JobResult(success=True)

    @property
    def webhook_payload_type(self) -> type:
        return InstrumentPayload
