import datetime
import uuid
from datetime import UTC

from sqlalchemy import delete, insert, or_, select, text, update
from sqlalchemy.engine import Engine

from pkgs.argument_parser import CachedParser
from pkgs.serialization_util import serialize_for_storage
from uncountable.integration.db.session import DBSessionMaker
from uncountable.integration.queue_runner.datastore.interface import Datastore
from uncountable.integration.queue_runner.datastore.model import Base, QueuedJob
from uncountable.types import queued_job_t

queued_job_payload_parser = CachedParser(queued_job_t.QueuedJobPayload)

MAX_QUEUE_WINDOW_DAYS = 30


class DatastoreSqlite(Datastore):
    def __init__(self, session_maker: DBSessionMaker) -> None:
        self.session_maker = session_maker
        super().__init__()

    @classmethod
    def setup(cls, engine: Engine) -> None:
        Base.metadata.create_all(engine)
        with engine.connect() as connection:
            if not bool(
                connection.execute(
                    text(
                        "select exists (select 1 from pragma_table_info('queued_jobs') where name='status');"
                    )
                ).scalar()
            ):
                connection.execute(
                    text("alter table queued_jobs add column status VARCHAR")
                )

    def add_job_to_queue(
        self, job_payload: queued_job_t.QueuedJobPayload, job_ref_name: str
    ) -> queued_job_t.QueuedJob:
        with self.session_maker() as session:
            serialized_payload = serialize_for_storage(job_payload)
            queued_job_uuid = str(uuid.uuid4())
            num_attempts = 0
            submitted_at = datetime.datetime.now(UTC)
            insert_stmt = insert(QueuedJob).values({
                QueuedJob.id.key: queued_job_uuid,
                QueuedJob.job_ref_name.key: job_ref_name,
                QueuedJob.payload.key: serialized_payload,
                QueuedJob.status.key: queued_job_t.JobStatus.QUEUED,
                QueuedJob.num_attempts: num_attempts,
                QueuedJob.submitted_at: submitted_at,
            })
            session.execute(insert_stmt)
            return queued_job_t.QueuedJob(
                queued_job_uuid=queued_job_uuid,
                job_ref_name=job_ref_name,
                payload=job_payload,
                status=queued_job_t.JobStatus.QUEUED,
                submitted_at=submitted_at,
                num_attempts=num_attempts,
            )

    def retry_job(
        self,
        queued_job_uuid: str,
    ) -> queued_job_t.QueuedJob | None:
        with self.session_maker() as session:
            select_stmt = select(
                QueuedJob.id,
                QueuedJob.payload,
                QueuedJob.num_attempts,
                QueuedJob.job_ref_name,
                QueuedJob.status,
                QueuedJob.submitted_at,
            ).filter(QueuedJob.id == queued_job_uuid)
            existing_job = session.execute(select_stmt).one_or_none()

            if (
                existing_job is None
                or existing_job.status != queued_job_t.JobStatus.FAILED
            ):
                return None

            update_stmt = (
                update(QueuedJob)
                .values({QueuedJob.status.key: queued_job_t.JobStatus.QUEUED})
                .filter(QueuedJob.id == queued_job_uuid)
            )
            session.execute(update_stmt)

            return queued_job_t.QueuedJob(
                queued_job_uuid=existing_job.id,
                job_ref_name=existing_job.job_ref_name,
                num_attempts=existing_job.num_attempts,
                status=queued_job_t.JobStatus.QUEUED,
                submitted_at=existing_job.submitted_at,
                payload=queued_job_payload_parser.parse_storage(existing_job.payload),
            )

    def increment_num_attempts(self, queued_job_uuid: str) -> int:
        with self.session_maker() as session:
            update_stmt = (
                update(QueuedJob)
                .values({QueuedJob.num_attempts.key: QueuedJob.num_attempts + 1})
                .filter(QueuedJob.id == queued_job_uuid)
            )
            session.execute(update_stmt)
            session.flush()
            # IMPROVE: python3's sqlite does not support the RETURNING clause
            select_stmt = select(QueuedJob.num_attempts).filter(
                QueuedJob.id == queued_job_uuid
            )
            return int(session.execute(select_stmt).one().num_attempts)

    def remove_job_from_queue(self, queued_job_uuid: str) -> None:
        with self.session_maker() as session:
            delete_stmt = delete(QueuedJob).filter(QueuedJob.id == queued_job_uuid)
            session.execute(delete_stmt)

    def update_job_status(
        self, queued_job_uuid: str, status: queued_job_t.JobStatus
    ) -> None:
        with self.session_maker() as session:
            update_stmt = (
                update(QueuedJob)
                .values({QueuedJob.status.key: status})
                .filter(QueuedJob.id == queued_job_uuid)
            )
            session.execute(update_stmt)

    def list_queued_job_metadata(
        self, offset: int = 0, limit: int | None = 100
    ) -> list[queued_job_t.QueuedJobMetadata]:
        with self.session_maker() as session:
            select_statement = (
                select(
                    QueuedJob.id,
                    QueuedJob.job_ref_name,
                    QueuedJob.num_attempts,
                    QueuedJob.status,
                    QueuedJob.submitted_at,
                )
                .order_by(QueuedJob.submitted_at)
                .offset(offset)
                .limit(limit)
            )

            queued_job_metadata: list[queued_job_t.QueuedJobMetadata] = [
                queued_job_t.QueuedJobMetadata(
                    queued_job_uuid=row.id,
                    job_ref_name=row.job_ref_name,
                    num_attempts=row.num_attempts,
                    status=row.status or queued_job_t.JobStatus.QUEUED,
                    submitted_at=row.submitted_at,
                )
                for row in session.execute(select_statement)
            ]

            return queued_job_metadata

    def get_next_queued_job_for_ref_name(
        self, job_ref_name: str
    ) -> queued_job_t.QueuedJob | None:
        with self.session_maker() as session:
            select_stmt = (
                select(
                    QueuedJob.id,
                    QueuedJob.payload,
                    QueuedJob.num_attempts,
                    QueuedJob.job_ref_name,
                    QueuedJob.status,
                    QueuedJob.submitted_at,
                )
                .filter(QueuedJob.job_ref_name == job_ref_name)
                .filter(
                    or_(
                        QueuedJob.status == queued_job_t.JobStatus.QUEUED,
                        QueuedJob.status.is_(None),
                    )
                )
                .limit(1)
                .order_by(QueuedJob.submitted_at)
            )

            for row in session.execute(select_stmt):
                parsed_payload = queued_job_payload_parser.parse_storage(row.payload)
                return queued_job_t.QueuedJob(
                    queued_job_uuid=row.id,
                    job_ref_name=row.job_ref_name,
                    num_attempts=row.num_attempts,
                    status=row.status or queued_job_t.JobStatus.QUEUED,
                    submitted_at=row.submitted_at,
                    payload=parsed_payload,
                )

            return None

    def load_job_queue(self) -> list[queued_job_t.QueuedJob]:
        with self.session_maker() as session:
            select_stmt = (
                select(
                    QueuedJob.id,
                    QueuedJob.payload,
                    QueuedJob.num_attempts,
                    QueuedJob.job_ref_name,
                    QueuedJob.status,
                    QueuedJob.submitted_at,
                )
                .filter(
                    or_(
                        QueuedJob.status == queued_job_t.JobStatus.QUEUED,
                        QueuedJob.status.is_(None),
                    )
                )
                .order_by(QueuedJob.submitted_at)
            )

            queued_jobs: list[queued_job_t.QueuedJob] = []
            for row in session.execute(select_stmt):
                parsed_payload = queued_job_payload_parser.parse_storage(row.payload)
                queued_jobs.append(
                    queued_job_t.QueuedJob(
                        queued_job_uuid=row.id,
                        job_ref_name=row.job_ref_name,
                        num_attempts=row.num_attempts,
                        status=row.status or queued_job_t.JobStatus.QUEUED,
                        submitted_at=row.submitted_at,
                        payload=parsed_payload,
                    )
                )

            return queued_jobs

    def vaccuum_queued_jobs(self) -> None:
        with self.session_maker() as session:
            delete_stmt = (
                delete(QueuedJob)
                .filter(QueuedJob.status == queued_job_t.JobStatus.QUEUED)
                .filter(
                    QueuedJob.submitted_at
                    <= (
                        datetime.datetime.now(UTC)
                        - datetime.timedelta(days=MAX_QUEUE_WINDOW_DAYS)
                    )
                )
            )
            session.execute(delete_stmt)
