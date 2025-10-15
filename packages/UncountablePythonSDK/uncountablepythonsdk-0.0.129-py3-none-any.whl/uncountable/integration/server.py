import signal
from dataclasses import asdict
from types import TracebackType
from typing import assert_never

from apscheduler.executors.pool import ThreadPoolExecutor
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.schedulers.base import BaseScheduler
from apscheduler.triggers.cron import CronTrigger
from opentelemetry.trace import get_current_span
from sqlalchemy.engine.base import Engine

from uncountable.core.environment import get_local_admin_server_port
from uncountable.integration.cron import CronJobArgs, cron_job_executor
from uncountable.integration.queue_runner.command_server.command_client import (
    send_vaccuum_queued_jobs_message,
)
from uncountable.integration.telemetry import Logger
from uncountable.types import base_t, job_definition_t
from uncountable.types.job_definition_t import (
    CronJobDefinition,
    HttpJobDefinitionBase,
)

_MAX_APSCHEDULER_CONCURRENT_JOBS = 1

VACCUUM_QUEUED_JOBS_JOB_ID = "vacuum_queued_jobs"

STATIC_JOB_IDS = {VACCUUM_QUEUED_JOBS_JOB_ID}


def vaccuum_queued_jobs() -> None:
    send_vaccuum_queued_jobs_message(port=get_local_admin_server_port())


class IntegrationServer:
    _scheduler: BaseScheduler
    _engine: Engine
    _server_logger: Logger

    def __init__(self, engine: Engine) -> None:
        self._engine = engine
        self._scheduler = BackgroundScheduler(
            timezone="UTC",
            jobstores={"default": SQLAlchemyJobStore(engine=engine)},
            executors={"default": ThreadPoolExecutor(_MAX_APSCHEDULER_CONCURRENT_JOBS)},
        )
        self._server_logger = Logger(get_current_span())

    def _register_static_jobs(self) -> None:
        all_job_ids = {job.id for job in self._scheduler.get_jobs()}
        if VACCUUM_QUEUED_JOBS_JOB_ID in all_job_ids:
            self._scheduler.remove_job(VACCUUM_QUEUED_JOBS_JOB_ID)

        self._scheduler.add_job(
            vaccuum_queued_jobs,
            max_instances=1,
            coalesce=True,
            trigger=CronTrigger.from_crontab("5 4 * * 4"),
            name="Vaccuum queued jobs",
            id=VACCUUM_QUEUED_JOBS_JOB_ID,
            kwargs={},
            misfire_grace_time=None,
        )

    def register_jobs(self, profiles: list[job_definition_t.ProfileMetadata]) -> None:
        valid_job_ids: set[str] = set()
        for profile_metadata in profiles:
            for job_defn in profile_metadata.jobs:
                valid_job_ids.add(job_defn.id)
                match job_defn:
                    case CronJobDefinition():
                        # Add to ap scheduler
                        job_kwargs = asdict(
                            CronJobArgs(
                                definition=job_defn, profile_metadata=profile_metadata
                            )
                        )
                        try:
                            existing_job = self._scheduler.get_job(job_defn.id)
                        except ValueError as e:
                            self._server_logger.log_warning(
                                f"could not reconstitute job {job_defn.id}: {e}"
                            )
                            self._scheduler.remove_job(job_defn.id)
                            existing_job = None
                        if existing_job is not None:
                            existing_job.modify(
                                name=job_defn.name,
                                kwargs=job_kwargs,
                                misfire_grace_time=None,
                            )
                            existing_job.reschedule(
                                CronTrigger.from_crontab(job_defn.cron_spec)
                            )
                            if not job_defn.enabled:
                                existing_job.pause()
                            else:
                                existing_job.resume()
                        else:
                            job_opts: dict[str, base_t.JsonValue] = {}
                            if not job_defn.enabled:
                                job_opts["next_run_time"] = None
                            self._scheduler.add_job(
                                cron_job_executor,
                                # IMPROVE: reconsider these defaults
                                max_instances=1,
                                coalesce=True,
                                trigger=CronTrigger.from_crontab(job_defn.cron_spec),
                                name=job_defn.name,
                                id=job_defn.id,
                                kwargs=job_kwargs,
                                misfire_grace_time=None,
                                **job_opts,
                            )
                    case HttpJobDefinitionBase():
                        pass
                    case _:
                        assert_never(job_defn)
        all_job_ids = {job.id for job in self._scheduler.get_jobs()}
        invalid_job_ids = all_job_ids.difference(valid_job_ids.union(STATIC_JOB_IDS))

        for job_id in invalid_job_ids:
            self._scheduler.remove_job(job_id)

    def serve_forever(self) -> None:
        signal.pause()

    def _start_apscheduler(self) -> None:
        self._scheduler.start()

    def _stop_apscheduler(self) -> None:
        self._scheduler.shutdown()

    def __enter__(self) -> "IntegrationServer":
        self._start_apscheduler()
        self._register_static_jobs()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        self._stop_apscheduler()
