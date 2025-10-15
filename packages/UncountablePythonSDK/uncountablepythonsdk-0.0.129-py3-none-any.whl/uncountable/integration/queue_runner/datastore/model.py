from sqlalchemy import JSON, BigInteger, Column, DateTime, Enum, Text
from sqlalchemy.orm import declarative_base
from sqlalchemy.sql import func

from uncountable.types import queued_job_t

Base = declarative_base()


class QueuedJob(Base):
    __tablename__ = "queued_jobs"

    id = Column(Text, primary_key=True)
    job_ref_name = Column(Text, nullable=False, index=True)
    submitted_at = Column(
        DateTime(timezone=True), server_default=func.current_timestamp(), nullable=False
    )
    payload = Column(JSON, nullable=False)
    num_attempts = Column(BigInteger, nullable=False, default=0, server_default="0")
    status = Column(
        Enum(queued_job_t.JobStatus, length=None),
        default=queued_job_t.JobStatus.QUEUED,
        nullable=True,
    )
