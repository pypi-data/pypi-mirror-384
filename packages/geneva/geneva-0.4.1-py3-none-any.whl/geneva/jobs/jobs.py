# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright The Geneva Authors

import base64
import enum
import json
import logging
import uuid
from datetime import datetime
from enum import Enum, unique
from typing import Optional

import attrs
import pyarrow as pa

from geneva.db import Connection
from geneva.utils import current_user, dt_now_utc, retry_lance
from geneva.utils.schema import alter_or_create_table

GENEVA_JOBS_TABLE_NAME = "geneva_jobs"

_LOG = logging.getLogger(__name__)


@unique
class JobStatus(Enum):
    """Status of a Job"""

    PENDING = "PENDING"
    RUNNING = "RUNNING"
    DONE = "DONE"
    FAILED = "FAILED"


@attrs.define(kw_only=True)
class JobRecord:
    """A Feature Engineering Job record.

    When a backfill or refresh is triggered, these records contain the job's details for
    history tracking and also provides references for jobs if they are still running
    so other users can track it.

    User should not directly construct this object.
    """

    table_name: str = attrs.field()
    column_name: str = attrs.field()
    job_id: str = attrs.field(factory=lambda: str(uuid.uuid4()))
    job_type: str = attrs.field(default="BACKFILL")
    object_ref: Optional[str] = attrs.field(default=None)
    status: JobStatus = attrs.field(
        default=JobStatus.PENDING, metadata={"pa_type": pa.string()}
    )
    launched_at: datetime = attrs.field(
        factory=lambda: dt_now_utc(), metadata={"pa_type": pa.timestamp("us", tz="UTC")}
    )
    completed_at: Optional[datetime] = attrs.field(
        default=None, metadata={"pa_type": pa.timestamp("us", tz="UTC")}
    )
    config: str = attrs.field(default="{}")

    # v0.2.x additions
    launched_by: Optional[str] = attrs.field(factory=current_user)

    # 0.4.x additions
    manifest_id: Optional[str] = attrs.field(default=None)
    manifest_checksum: Optional[str] = attrs.field(default=None)


def _safe_job_record(jr_dict: dict) -> JobRecord:
    """Create JobRecord from dict, ignoring unknown fields for forward compatibility.

    This allows old clients to read tables with new columns they don't understand.
    """
    known_fields = {f.name for f in attrs.fields(JobRecord)}
    filtered = {k: v for k, v in jr_dict.items() if k in known_fields}
    return JobRecord(**filtered)


class JobStateManager:
    def __init__(
        self, genevadb: Connection, jobs_table_name=GENEVA_JOBS_TABLE_NAME
    ) -> None:
        self.jobs_db = genevadb
        self.jobs_table = alter_or_create_table(
            genevadb,
            jobs_table_name,
            JobRecord(table_name="dummytable", column_name="dummycol"),
        )

    @retry_lance
    def launch(self, table_name: str, column_name: str, **kwargs) -> JobRecord:
        args = kwargs.copy()
        args.pop("udf", None)  # Remove the udf argument (TODO serialized it)

        # Extract manifest fields if provided
        manifest_id = args.pop("manifest_id", None)
        manifest_checksum = args.pop("manifest_checksum", None)

        jr = JobRecord(
            table_name=table_name,
            column_name=column_name,
            config=json.dumps(args),
            manifest_id=manifest_id,
            manifest_checksum=manifest_checksum,
        )
        self.jobs_table.add(
            [
                attrs.asdict(
                    jr,
                    value_serializer=lambda obj, a, v: v.value
                    if isinstance(v, enum.Enum)
                    else v,
                )
            ]
        )
        return jr

    @retry_lance
    def set_object_ref(self, job_id: str, object_ref: bytes) -> None:
        self.jobs_table._ltbl.update(
            where=f"job_id = '{job_id}'",
            # TODO why can't lance handle bytes in an update directly?
            values={
                "object_ref": base64.b64encode(object_ref).decode("utf-8"),
            },
        )

    @retry_lance
    def _set_status(self, job_id: str, status: JobStatus) -> None:
        self.jobs_table._ltbl.update(
            where=f"job_id = '{job_id}'",
            values={
                "status": status.value,
            },
        )

    def set_running(self, job_id: str) -> None:
        self._set_status(job_id, JobStatus.RUNNING)

    def set_failed(self, job_id: str, msg: str) -> None:
        # TODO add msg to the record
        self._set_status(job_id, JobStatus.FAILED)

    @retry_lance
    def list_active(self, table_name: str | None = None) -> list[JobRecord]:
        # TODO: Currently need to use tbl._ltbl.search() instead of tbl.search()
        # because geneva table semantics are not consistent with lancedb's currently
        known_cols = [f.name for f in attrs.fields(JobRecord)]
        wheres = ["status == 'RUNNING'"]
        if table_name:
            wheres.append(f"table_name = '{table_name}'")
        jrs = (
            self.jobs_table._ltbl.search()
            .where(" and ".join(wheres))
            .select(known_cols)
            .to_arrow()
            .to_pylist()
        )
        return [_safe_job_record(jr) for jr in jrs]

    @retry_lance
    def get(self, job_id: str) -> list[JobRecord]:
        # TODO: Currently need to use tbl._ltbl.search() instead of tbl.search()
        # because geneva table semantics are not consistent with lancedb's currently

        # Need to get latest because updates can come from other processes
        self.jobs_table._ltbl.checkout_latest()
        known_cols = [f.name for f in attrs.fields(JobRecord)]
        q = (
            self.jobs_table._ltbl.search()
            .where(f"job_id = '{job_id}'")
            .select(known_cols)
        )
        return [_safe_job_record(jr) for jr in q.to_arrow().to_pylist()]

    @retry_lance
    def set_completed(self, job_id: str, status: str = "DONE") -> None:
        self.jobs_table._ltbl.update(
            where=f"job_id = '{job_id}'",
            values={
                "status": status,
                "completed_at": dt_now_utc(),
            },
        )
