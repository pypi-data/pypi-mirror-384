# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright The Geneva Authors

import contextlib
import functools
import hashlib
import json
import logging
import random
import time
import uuid
from collections import Counter
from collections.abc import Generator, Iterator
from typing import Any, cast

import attrs
import cloudpickle
import lance
import pyarrow as pa
import ray.actor
import ray.exceptions
import ray.util.queue
from pyarrow.fs import FileSystem
from ray.actor import ActorHandle
from tqdm.std import tqdm as TqdmType  # noqa: N812

from geneva.apply import (
    CheckpointingApplier,
    plan_copy,
    plan_read,
)
from geneva.apply.applier import BatchApplier
from geneva.apply.multiprocess import MultiProcessBatchApplier
from geneva.apply.simple import SimpleApplier
from geneva.apply.task import BackfillUDFTask, CopyTableTask, MapTask, ReadTask
from geneva.checkpoint import CheckpointStore
from geneva.debug.logger import CheckpointStoreErrorLogger
from geneva.jobs.config import JobConfig
from geneva.packager import UDFPackager, UDFSpec
from geneva.query import (
    MATVIEW_META_BASE_DBURI,
    MATVIEW_META_BASE_TABLE,
    MATVIEW_META_BASE_VERSION,
    MATVIEW_META_QUERY,
    GenevaQuery,
    GenevaQueryBuilder,
)
from geneva.runners.ray.actor_pool import ActorPool
from geneva.runners.ray.jobtracker import JobTracker
from geneva.runners.ray.kuberay import _ray_status
from geneva.runners.ray.raycluster import CPU_ONLY_NODE, ray_tqdm
from geneva.runners.ray.writer import FragmentWriter
from geneva.table import JobFuture, Table, TableReference
from geneva.tqdm import tqdm
from geneva.transformer import UDF

_LOG = logging.getLogger(__name__)


REFRESH_EVERY_SECONDS = 5.0

CNT_WORKERS_PENDING = "cnt_geneva_workers_pending"
CNT_WORKERS_ACTIVE = "cnt_geneva_workers_active"
CNT_RAY_NODES = "cnt_ray_nodes"
CNT_K8S_NODES = "k8s_nodes_provisioned"
CNT_K8S_PHASE = "k8s_cluster_phase"


@ray.remote  # type: ignore[misc]
@attrs.define
class ApplierActor:  # pyright: ignore[reportRedeclaration]
    applier: CheckpointingApplier

    def __ray_ready__(self) -> None:
        pass

    def run(self, task) -> tuple[ReadTask, str]:
        return task, self.applier.run(task)


ApplierActor: ray.actor.ActorClass = cast("ray.actor.ActorClass", ApplierActor)  # type: ignore[no-redef]


def _get_fragment_dedupe_key(uri: str, frag_id: int, map_task: MapTask) -> str:
    key = f"{uri}:{frag_id}:{map_task.checkpoint_key()}"
    return hashlib.sha256(key.encode()).hexdigest()


def _run_column_adding_pipeline(
    map_task: MapTask,
    checkpoint_store: CheckpointStore,
    config: JobConfig,
    dst: TableReference,
    input_plan: Iterator[ReadTask],
    job_id: str | None,
    applier_concurrency: int = 8,
    *,
    intra_applier_concurrency: int = 1,
    use_cpu_only_pool: bool = False,
    job_tracker=None,
    where=None,
    skipped_fragments: dict | None = None,
    skipped_stats: dict | None = None,
) -> None:
    """
    Run the column adding pipeline.

    Args:
    * use_cpu_only_pool: If True will force schedule cpu-only actors on cpu-only nodes.

    """
    job_id = job_id or uuid.uuid4().hex
    job_tracker = job_tracker or JobTracker.options(
        name=f"jobtracker-{job_id}",
        num_cpus=0.1,
        memory=128 * 1024 * 1024,
        max_restarts=-1,
    ).remote(job_id)
    job = ColumnAddPipelineJob(
        map_task=map_task,
        checkpoint_store=checkpoint_store,
        config=config,
        dst=dst,
        input_plan=input_plan,
        job_id=job_id,
        applier_concurrency=applier_concurrency,
        intra_applier_concurrency=intra_applier_concurrency,
        use_cpu_only_pool=use_cpu_only_pool,
        job_tracker=job_tracker,  # type: ignore[arg-type]
        where=where,
        skipped_fragments=skipped_fragments or {},
        skipped_stats=skipped_stats or {},
    )
    job.run()


@attrs.define
class ColumnAddPipelineJob:
    """ColumnAddPipeline drives batches of rows to commits in the dataset.

    ReadTasks are defined wrapped for tracking, and then dispatched for udf exeuction
    in the ActorPool.  The results are sent to the FragmentWriterManager which
    manages fragment checkpoints and incremental commits.
    """

    map_task: MapTask
    checkpoint_store: CheckpointStore
    config: JobConfig
    dst: TableReference
    input_plan: Iterator[ReadTask]
    job_id: str
    applier_concurrency: int = 8
    intra_applier_concurrency: int = 1
    use_cpu_only_pool: bool = False
    job_tracker: ActorHandle | None = None
    where: str | None = None
    skipped_fragments: dict = attrs.field(factory=dict)
    skipped_stats: dict = attrs.field(factory=dict)
    _total_rows: int = attrs.field(default=0, init=False)
    _last_status_refresh: float = attrs.field(factory=lambda: 0.0, init=False)

    def setup_inputplans(self) -> tuple[Iterator[ReadTask], Counter[int], int]:
        all_tasks = list(self.input_plan)
        self.job_tracker = self.job_tracker or JobTracker.options(  # type: ignore[assignment]
            name=f"jobtracker-{self.job_id}",
            num_cpus=0.1,
            memory=128 * 1024 * 1024,
            max_restarts=-1,
        ).remote(self.job_id)

        self._total_rows = sum(t.num_rows() for t in all_tasks)
        plan_len = len(all_tasks)

        # fragments
        if self.job_tracker is not None:
            self.job_tracker.set_total.remote("fragments", plan_len)
            self.job_tracker.set_desc.remote(
                "fragments",
                f"[{self.dst.table_name} - {self.map_task.name()}] Batches scheduled",
            )

        # this reports # of batches started, not completed.
        tasks_by_frag = Counter(t.dest_frag_id() for t in all_tasks)
        return (
            ray_tqdm(all_tasks, self.job_tracker, metric="fragments"),
            tasks_by_frag,
            plan_len,
        )

    def setup_actor(self) -> ray.actor.ActorHandle:
        actor = ApplierActor

        # actor.options can only be called once, we must pass all override args
        # in one shot
        num_cpus = self.map_task.num_cpus()
        args = {
            "num_cpus": (num_cpus or 1) * self.intra_applier_concurrency,
        }
        num_gpus = self.map_task.num_gpus()
        if num_gpus and num_gpus > 0:
            args["num_gpus"] = num_gpus
        elif self.use_cpu_only_pool:
            _LOG.info("Using CPU only pool for applier, setting %s to 1", CPU_ONLY_NODE)
            args["resources"] = {CPU_ONLY_NODE: 1}  # type: ignore[assignment]
        memory = self.map_task.memory()
        if memory:
            args["memory"] = memory * self.intra_applier_concurrency
        actor = actor.options(**args)  # type: ignore[attr-defined]
        return actor  # type: ignore[return-value]

    def setup_batchapplier(self) -> BatchApplier:
        if self.intra_applier_concurrency > 1:
            return MultiProcessBatchApplier(
                num_processes=self.intra_applier_concurrency
            )
        else:
            return SimpleApplier()

    def setup_actorpool(self) -> ActorPool:
        batch_applier = self.setup_batchapplier()

        applier = CheckpointingApplier(
            map_task=self.map_task,
            batch_applier=batch_applier,
            checkpoint_uri=self.checkpoint_store.uri(),
            error_logger=CheckpointStoreErrorLogger(self.job_id, self.checkpoint_store),
        )

        actor = self.setup_actor()
        if self.job_tracker is not None:
            self.job_tracker.set_total.remote("workers", self.applier_concurrency)
            self.job_tracker.set_desc.remote("workers", "Workers started")

        pool = ActorPool(
            functools.partial(actor.remote, applier=applier),
            self.applier_concurrency,
            job_tracker=self.job_tracker,
            worker_metric="workers",
        )
        return pool

    def setup_writertracker(self) -> tuple[lance.LanceDataset, int]:
        ds = self.dst.open().to_lance()
        fragments = ds.get_fragments()
        len_frags = len(fragments)

        if self.job_tracker is not None:
            self.job_tracker.set_total.remote("writer_fragments", len_frags)
            self.job_tracker.set_desc.remote("writer_fragments", "Fragments written")
        ray_tqdm(fragments, self.job_tracker, metric="writer_fragments")

        return ds, len_frags

    def _refresh_cluster_status(self) -> None:
        # cluster metrics
        try:
            ray_status = _ray_status()

            # TODO batch this.
            if self.job_tracker is not None:
                m_rn = CNT_RAY_NODES
                cnt_workers = ray_status.get(m_rn, 0)
                self.job_tracker.set_desc.remote(m_rn, "ray nodes provisioned")
                self.job_tracker.set.remote(m_rn, cnt_workers)

                # TODO separate metrics for gpu and cpu workers?
                m_caa = CNT_WORKERS_ACTIVE
                cnt_active = ray_status.get(m_caa, 0)
                self.job_tracker.set_desc.remote(m_caa, "active workers")
                self.job_tracker.set_total.remote(m_caa, self.applier_concurrency)
                self.job_tracker.set.remote(m_caa, cnt_active)

                m_cpa = CNT_WORKERS_PENDING
                cnt_pending = ray_status.get(m_cpa, 0)
                self.job_tracker.set_desc.remote(m_cpa, "pending workers")
                self.job_tracker.set_total.remote(m_cpa, self.applier_concurrency)
                self.job_tracker.set.remote(m_cpa, cnt_pending)

        except Exception:
            _LOG.debug("refresh: failed to get ray status", exc_info=True)
            # do nothing

    def _try_refresh_cluster_status(self) -> None:
        now = time.monotonic()
        if now - self._last_status_refresh >= REFRESH_EVERY_SECONDS:
            self._refresh_cluster_status()
            self._last_status_refresh = now

    def run(self) -> None:
        plans, tasks_by_frag, cnt_batches = self.setup_inputplans()
        pool = self.setup_actorpool()
        ds, cnt_fragments = self.setup_writertracker()

        prefix = (
            f"[{self.dst.table_name} - {self.map_task.name()} "
            f"({cnt_fragments} fragments)]"
        )

        try:
            self._refresh_cluster_status()
        except Exception:
            _LOG.debug("initial cluster status refresh failed", exc_info=True)
            # do nothing

        # formatting to show fragments
        try:
            cg = (
                int(self.config.commit_granularity)
                if self.config.commit_granularity is not None
                else 0
            )
        except Exception:
            cg = 0
        cg = max(cg, 0)
        cgstr = (
            "(commit at completion)"
            if cg == 0
            else f"(every {cg} fragment{'s' if cg != 1 else ''})"
        )
        # rows metrics (all cumulative)
        if self.job_tracker is not None:
            # Get the full dataset total (including skipped fragments)
            dataset_total_rows = self._total_rows
            # skipped_stats is {'fragments': count, 'rows': count} for
            # progress tracking.
            if self.skipped_stats:
                dataset_total_rows += self.skipped_stats.get("rows", 0)

            skipped_rows = self.skipped_stats.get("rows", 0)

            previously_completed = (
                f" ({skipped_rows} previously completed)" if skipped_rows > 0 else ""
            )
            for m, desc in [
                (
                    "rows_checkpointed",
                    f"{prefix} Rows checkpointed{previously_completed}",
                ),
                (
                    "rows_ready_for_commit",
                    f"{prefix} Rows ready for commit",
                ),
                (
                    "rows_committed",
                    f"{prefix} Rows committed {cgstr}",
                ),
            ]:
                self.job_tracker.set_total.remote(m, dataset_total_rows)
                self.job_tracker.set_desc.remote(m, desc)
                # Initialize with skipped rows as already completed
                if skipped_rows > 0:
                    self.job_tracker.set.remote(m, skipped_rows)

        _LOG.info(
            f"Pipeline executing on {cnt_batches} batches over "
            f"{cnt_fragments} table fragments"
        )

        # kick off the applier actors
        applier_iter = pool.map_unordered(
            lambda actor, value: actor.run.remote(value),
            # the API says list, but iterables are fine
            plans,
        )

        fwm = FragmentWriterManager(
            ds.version,
            ds_uri=ds.uri,
            map_task=self.map_task,
            checkpoint_store=self.checkpoint_store,
            where=self.where,
            job_tracker=self.job_tracker,
            commit_granularity=self.config.commit_granularity,
            expected_tasks=dict(tasks_by_frag),
            skipped_fragments=self.skipped_fragments or {},
        )

        for task, result in applier_iter:
            fwm.ingest(result, task)
            # ensure we discover any frgments that finished writing even if the
            # current task belongs to another fragment.
            fwm.poll_all()
            self._try_refresh_cluster_status()

        pool.shutdown()
        fwm.cleanup()
        with contextlib.suppress(Exception):
            self._refresh_cluster_status()


@attrs.define
class FragmentWriterSession:
    """This tracks all the batch tasks for a single fragment.

    It is responsible for managing the fragment writer's life cycle and does the
    bookkeeping of inflight tasks, completed tasks, and the queue of tasks to write.
    These are locally tracked and accounted for before the fragment is considered
    complete and ready to be commited to the dataset.

    It expects to be initialized and then fed with `ingest_task` calls. After all tasks
    have been added, it is `seal`ed meaning no more input tasks are expected.  Then it
    can be `drain`ed to yield all completed tasks.
    """

    frag_id: int
    ds_uri: str
    output_columns: list[str]
    checkpoint_store: CheckpointStore
    where: str | None

    # runtime state.  This is single-threaded and is not thread-safe.
    queue: ray.util.queue.Queue = attrs.field(factory=ray.util.queue.Queue, init=False)
    actor: ActorHandle = attrs.field(init=False)
    cached_tasks: list[tuple[int, Any]] = attrs.field(factory=list, init=False)
    inflight: dict[ray.ObjectRef, int] = attrs.field(factory=dict, init=False)
    _shutdown: bool = attrs.field(default=False, init=False)

    sealed: bool = attrs.field(default=False, init=False)  # no more tasks will be added
    enqueued: int = attrs.field(default=0, init=False)  # total expected tasks
    completed: int = attrs.field(default=0, init=False)  # total compelted tasks

    def __attrs_post_init__(self) -> None:
        self._start_writer()

    def _start_writer(self) -> None:
        self.actor = FragmentWriter.options(  # type: ignore[assignment]
            num_cpus=0.1,  # make it cheap to schedule (not require full cpu)
            memory=1024 * 1024 * 1024,  # 1gb ram
        ).remote(
            self.ds_uri,
            self.output_columns,
            self.checkpoint_store.uri(),
            self.frag_id,
            self.queue,
            where=self.where,
        )
        # prime one future so we can detect when it finishes
        fut = self.actor.write.remote()
        self.inflight[fut] = self.frag_id

    def shutdown(self) -> None:
        len_inflight = len(self.inflight)
        if len_inflight > 0:
            try:
                is_empty = self.queue.empty()
            except (ray.exceptions.RayError, Exception):
                # queue actor died or unavailble.  assume empty
                is_empty = True
                # queue should be empty and inflight should be 0.
                _LOG.warning(
                    "Shutting down frag %s - queue empty %s, inflight: %d",
                    self.frag_id,
                    is_empty,
                    len_inflight,
                )

        if self._shutdown:
            return  # idempotent
        self.queue.shutdown()
        ray.kill(self.actor)
        self._shutdown = True

    def _restart(self) -> None:
        self.shutdown()

        # make it cheap to schedule (not require full cpu, reserve 256MiB ram)
        self.queue = ray.util.queue.Queue(
            actor_options={"num_cpus": 0.1, "memory": 256 * 1024 * 1024}
        )
        self.inflight.clear()
        self.cached_tasks, old_tasks = [], self.cached_tasks
        self.__attrs_post_init__()  # recreates writer & first future

        # replay tasks
        for off, res in old_tasks:
            self.queue.put((off, res))

    def ingest_task(self, offset: int, result: Any) -> None:
        """Called by manager when a new (offset, result) arrives."""
        self.cached_tasks.append((offset, result))
        self.enqueued += 1
        try:
            self.queue.put((offset, result))
        except (ray.exceptions.ActorDiedError, ray.exceptions.ActorUnavailableError):
            _LOG.warning("Writer actor for frag %s died – restarting", self.frag_id)
            self._restart()

    def poll_ready(self) -> list[tuple[int, Any, int]]:
        """Non‑blocking check for any finished futures.
        Returns list of (frag_id, new_file, rows_written) that completed."""
        ready, _ = ray.wait(list(self.inflight.keys()), timeout=0.0)
        completed: list[tuple[int, Any, int]] = []

        for fut in ready:
            try:
                res = ray.get(fut)
                assert isinstance(res, tuple) and len(res) == 3, (  # noqa: PT018
                    "FragmentWriter.write() should return (frag_id, new_file,"
                    " rows_written), "
                )
                fid, new_file, rows_written = res
                completed.append((fid, new_file, rows_written))
            except (
                ray.exceptions.ActorDiedError,
                ray.exceptions.ActorUnavailableError,
            ):
                _LOG.warning(
                    "Writer actor for frag %s unavailable – restarting", self.frag_id
                )
                self._restart()
                return []  # will show up next poll
            assert fid == self.frag_id
            self.completed += 1
            self.inflight.pop(fut)

        return completed

    def seal(self) -> None:
        self.sealed = True

    def drain(self) -> Generator[tuple[int, Any, int], None, None]:
        """Yield all (frag_id,new_file, rows_written) as futures complete."""
        while self.inflight:
            ready, _ = ray.wait(list(self.inflight.keys()), timeout=5.0)
            if not ready:
                continue

            for fut in ready:
                try:
                    res = ray.get(fut)
                    assert isinstance(res, tuple) and len(res) == 3, (  # noqa: PT018
                        "FragmentWriter.write() should return (frag_id, new_file,"
                        " rows_written), "
                    )
                    fid, new_file, rows_written = res
                    yield fid, new_file, rows_written
                    self.completed += 1
                except (
                    ray.exceptions.ActorDiedError,
                    ray.exceptions.ActorUnavailableError,
                ):
                    _LOG.warning(
                        "Writer actor for frag %s died during drain—restarting",
                        self.frag_id,
                    )
                    # clear out any old futures, spin up a fresh actor & queue
                    self._restart()
                    # break out to re-enter the while loop with a clean slate
                    break
                # sucessful write
                self.inflight.pop(fut)


@attrs.define
class FragmentWriterManager:
    """FragmentWriterManager is responsible for writing out fragments
    from the ReadTasks to the destination dataset.

    There is one instance so that we can track pending completed fragments and do
    partial commits.
    """

    dst_read_version: int
    ds_uri: str
    map_task: MapTask
    checkpoint_store: CheckpointStore
    where: str | None
    job_tracker: ActorHandle | None
    commit_granularity: int
    expected_tasks: dict[int, int]  # frag_id, # batches
    # int key is frag_id
    skipped_fragments: dict[int, lance.fragment.DataFile] = attrs.field(factory=dict)

    # internal state
    sessions: dict[int, FragmentWriterSession] = attrs.field(factory=dict, init=False)
    remaining_tasks: dict[int, int] = attrs.field(init=False)
    output_columns: list[str] = attrs.field(init=False)
    # Track fragment IDs that are skipped to avoid double-counting in progress
    _skipped_fragment_ids: set[int] = attrs.field(factory=set, init=False)
    # (frag_id, lance.fragment.DataFile, # rows)
    rows_input_by_frag: dict[int, int] = attrs.field(factory=dict, init=False)
    to_commit: list[tuple[int, lance.fragment.DataFile, int]] = attrs.field(
        factory=list, init=False
    )

    def __attrs_post_init__(self) -> None:
        # all output cols except for _rowaddr because it is implicit since the
        # lancedatafile is writing out in sequential order
        self.output_columns = [
            f.name for f in self.map_task.output_schema() if f.name != "_rowaddr"
        ]
        self.remaining_tasks = dict(self.expected_tasks)

        # Immediately add skipped fragments to commit list and update progress tracking
        total_skipped_rows = 0
        for frag_id, data_file in self.skipped_fragments.items():
            # Estimate row count from original fragment if available
            try:
                dataset = lance.dataset(self.ds_uri)
                original_fragment = dataset.get_fragment(frag_id)
                if original_fragment is None:
                    row_count = 0
                else:
                    row_count = original_fragment.count_rows()
                    # Note: we ignore where filters since we care about rows in the
                    # fragment
            except Exception:
                row_count = 0  # Default if we can't get the count

            self.to_commit.append((frag_id, data_file, row_count))
            self._skipped_fragment_ids.add(
                frag_id
            )  # Track that this fragment is skipped
            total_skipped_rows += row_count
            _LOG.info(
                f"Added skipped fragment {frag_id} to commit list with {row_count} rows"
            )

    def poll_all(self) -> None:
        for sess in list(self.sessions.values()):
            for fid, new_file, rows_written in sess.poll_ready():
                self._record_fragment(
                    fid, new_file, self.commit_granularity, rows_written
                )

    def ingest(self, result, task) -> None:
        frag_id = task.dest_frag_id()

        sess = self.sessions.get(frag_id)
        if sess is None:
            _LOG.debug("Creating writer for fragment %d", frag_id)
            sess = FragmentWriterSession(
                frag_id=frag_id,
                ds_uri=self.ds_uri,
                output_columns=self.output_columns,
                checkpoint_store=self.checkpoint_store,
                where=self.where,
            )
            self.sessions[frag_id] = sess

        sess.ingest_task(task.dest_offset(), result)
        try:
            num_rows = getattr(task, "num_rows", None)
            if callable(num_rows):
                num_rows = num_rows()
            if isinstance(num_rows, int) and num_rows > 0 and self.job_tracker:
                self.job_tracker.increment.remote("rows_checkpointed", num_rows)
                self.rows_input_by_frag[frag_id] = self.rows_input_by_frag.get(
                    frag_id, 0
                ) + int(num_rows)
        except Exception:
            _LOG.exception("Failed to get number of rows from result for task %s", task)
        self.remaining_tasks[frag_id] -= 1
        if self.remaining_tasks[frag_id] <= 0:
            sess.seal()

        # TODO check if previously checkpointed fragment exists

    def _record_fragment(
        self,
        frag_id: int,
        new_file,
        commit_granularity: int,
        rows_written: int,
    ) -> None:
        dedupe_key = _get_fragment_dedupe_key(self.ds_uri, frag_id, self.map_task)
        # store file name in case of a failure or delete and recalc reuse.
        self.checkpoint_store[dedupe_key] = pa.RecordBatch.from_pydict(
            {"file": new_file.path}
        )
        if self.job_tracker:
            self.job_tracker.increment.remote("writer_fragments", 1)

        input_rows = int(self.rows_input_by_frag.get(frag_id, 0))

        # Check if this fragment is already in the commit list (as a skipped fragment)
        existing_index = None
        for i, (existing_frag_id, _existing_file, _existing_rows) in enumerate(
            self.to_commit
        ):
            if existing_frag_id == frag_id:
                existing_index = i
                break

        if existing_index is not None:
            # Fragment already exists (was skipped), update the DataFile
            _LOG.info(
                f"Updating existing fragment {frag_id} in commit list "
                f"(was skipped, now processed)"
            )
            self.to_commit[existing_index] = (frag_id, new_file, input_rows)
            # Skipped fragments are not counted in rows_ready_for_commit since they
            # use existing checkpointed data rather than newly processed data
        else:
            # New fragment, add it normally
            _LOG.info(f"Adding new fragment {frag_id} to commit list")
            self.to_commit.append((frag_id, new_file, input_rows))
            if input_rows > 0 and self.job_tracker:
                self.job_tracker.increment.remote("rows_ready_for_commit", input_rows)

        # Track processed writes and hybrid-shutdown
        sess = self.sessions.get(frag_id)
        if sess and sess.sealed and not sess.inflight:
            # flush any pending commit for this fragment
            sess.shutdown()
            self.sessions.pop(frag_id, None)

        self._commit_if_n_fragments(commit_granularity)

    # aka _try_commit
    def _commit_if_n_fragments(
        self, commit_granularity: int, robust: bool = False
    ) -> None:
        """Commit fragments if we have enough to meet granularity threshold.

        Args:
            commit_granularity: Minimum number of fragments to commit
            robust: If True, retry RuntimeError with 'Too many concurrent writers'
        """
        n = max(1, int(commit_granularity))
        if len(self.to_commit) < n:
            return

        to_commit = self.to_commit
        self.to_commit = []
        version = self.dst_read_version
        operation = lance.LanceOperation.DataReplacement(
            replacements=[
                lance.LanceOperation.DataReplacementGroup(
                    fragment_id=frag_id,
                    new_file=new_file,
                )
                for frag_id, new_file, _rows in to_commit
            ]
        )

        retry_attempt = 0
        max_retries = 7 if robust else 0
        commit_type = "Robust" if robust else "Standard"

        while True:
            try:
                _LOG.info(
                    "%s commit: %d fragments to %s at version %d%s",
                    commit_type,
                    len(to_commit),
                    self.ds_uri,
                    version,
                    f" (attempt {retry_attempt + 1})"
                    if robust and retry_attempt > 0
                    else "",
                )
                lance.LanceDataset.commit(self.ds_uri, operation, read_version=version)
                # rows committed == sum(input rows for fragments just committed)
                # Exclude skipped fragments since they were already counted in
                # "ready for commit"
                committed_rows = sum(
                    _rows
                    for _fid, _new_file, _rows in to_commit
                    if _fid not in self._skipped_fragment_ids
                )
                if committed_rows and self.job_tracker:
                    self.job_tracker.increment.remote("rows_committed", committed_rows)

                if robust and retry_attempt > 0:
                    _LOG.info(
                        "%s commit succeeded after %d attempts",
                        commit_type,
                        retry_attempt + 1,
                    )
                break
            except OSError as e:
                # Conflict error has this message:
                # OSError: Commit conflict for version 6: This DataReplacement \
                # transaction is incompatible with concurrent transaction \
                # DataReplacement at version 6.,
                if "Commit conflict for version" not in str(e):
                    # only handle version conflict
                    raise e

                # WARNING - the versions are sequentially increasing and we assume we'll
                # eventually find a version that will not conflict.  This could be a
                # problem for rare cases where column replacements happen concurrently.

                # TODO: This is a workaround for now, but we should consider adding
                # conflict resolution to lance.

                # this is a version conflict, retry with next version
                _LOG.warning(
                    (
                        "%s commit failed with version conflict: %s. "
                        "Retrying with next version."
                    ),
                    commit_type,
                    e,
                )
                version += 1
            except RuntimeError as e:
                # Handle "Too many concurrent writers" errors from Lance
                # Only retry in robust mode
                if not robust or "Too many concurrent writers" not in str(e):
                    # only handle concurrent writers error in robust mode
                    raise e

                retry_attempt += 1
                if retry_attempt >= max_retries:
                    _LOG.error(
                        (
                            "%s commit failed after %d attempts with concurrent "
                            "writers error: %s"
                        ),
                        commit_type,
                        retry_attempt,
                        e,
                    )
                    raise e

                _LOG.warning(
                    (
                        "%s commit failed with concurrent writers (attempt %d/%d): %s. "
                        "Retrying with backoff."
                    ),
                    commit_type,
                    retry_attempt,
                    max_retries,
                    e,
                )
                # Use exponential backoff with jitter for concurrent writers
                backoff = min(30.0, 0.5 * (2 ** min(5, retry_attempt)))
                backoff += random.uniform(0, backoff * 0.1)  # Add 10% jitter
                time.sleep(backoff)

    def cleanup(self) -> None:
        _LOG.debug("draining & shutting down any leftover sessions")

        # 1) Commit any top‑of‑buffer fragments with robust retry logic
        self._commit_if_n_fragments(1, robust=True)

        # 2) Drain & shutdown whatever sessions remain
        for _frag_id, sess in list(self.sessions.items()):
            for fid, new_file, rows_written in sess.drain():
                # this may in turn pop more sessions via _record_fragment
                self._record_fragment(
                    fid, new_file, self.commit_granularity, rows_written
                )
            sess.shutdown()

        # 3) Clear out any sessions that finished in the loop above
        self.sessions.clear()

        # 4) Final safety commit of anything left with robust retry logic
        self._commit_if_n_fragments(1, robust=True)


def fetch_udf(table: Table, column_name: str) -> UDFSpec:
    schema = table._ltbl.schema
    field = schema.field(column_name)
    if field is None:
        raise ValueError(f"Column {column_name} not found in table {table}")

    udf_path = metadata_value("virtual_column.udf", field.metadata)
    fs, root_uri = FileSystem.from_uri(table.to_lance().uri)
    udf_payload = fs.open_input_file(f"{root_uri}/{udf_path}").read()

    udf_name = metadata_value("virtual_column.udf_name", field.metadata)
    udf_backend = metadata_value("virtual_column.udf_backend", field.metadata)

    return UDFSpec(
        name=udf_name,
        backend=udf_backend,
        udf_payload=udf_payload,
    )


def metadata_value(key: str, metadata: dict[bytes, bytes] | None) -> str:
    if metadata is None:
        raise ValueError(f"Metadata is None, cannot find key {key}")
    value = metadata.get(key.encode("utf-8"))
    if value is None:
        raise ValueError(f"Metadata key {key} not found in metadata {metadata}")
    return value.decode("utf-8")


def run_ray_copy_table(
    dst: TableReference,
    packager: UDFPackager,
    checkpoint_store: CheckpointStore | None = None,
    *,
    job_id: str | None = None,
    concurrency: int = 8,
    batch_size: int | None = None,
    task_shuffle_diversity: int | None = None,
    commit_granularity: int | None = None,
    **kwargs,
) -> None:
    # prepare job parameters
    config = JobConfig.get().with_overrides(
        batch_size=batch_size,
        task_shuffle_diversity=task_shuffle_diversity,
        commit_granularity=commit_granularity,
    )

    checkpoint_store = checkpoint_store or config.make_checkpoint_store()

    dst_schema = dst.open().schema
    if dst_schema.metadata is None:
        raise Exception("Destination dataset must have view metadata.")
    src_dburi = dst_schema.metadata[MATVIEW_META_BASE_DBURI.encode("utf-8")].decode(
        "utf-8"
    )
    src_name = dst_schema.metadata[MATVIEW_META_BASE_TABLE.encode("utf-8")].decode(
        "utf-8"
    )
    src_version = int(
        dst_schema.metadata[MATVIEW_META_BASE_VERSION.encode("utf-8")].decode("utf-8")
    )
    src = TableReference(db_uri=src_dburi, table_name=src_name, version=src_version)
    query_json = dst_schema.metadata[MATVIEW_META_QUERY.encode("utf-8")]
    query = GenevaQuery.model_validate_json(query_json)

    src_table = src.open()
    schema = GenevaQueryBuilder.from_query_object(src_table, query).schema

    job_id = job_id or uuid.uuid4().hex

    column_udfs = query.extract_column_udfs(packager)

    # take all cols (excluding some internal columns) since contents are needed to feed
    # udfs or copy src table data
    input_cols = [
        n for n in src_table.schema.names if n not in ["__is_set", "__source_row_id"]
    ]

    plan = plan_copy(
        src,
        dst,
        input_cols,
        batch_size=config.batch_size,
        task_shuffle_diversity=config.task_shuffle_diversity,
    )

    map_task = CopyTableTask(
        column_udfs=column_udfs, view_name=dst.table_name, schema=schema
    )

    _run_column_adding_pipeline(
        map_task,
        checkpoint_store,
        config,
        dst,
        plan,
        job_id,
        concurrency,
        **kwargs,
    )


def dispatch_run_ray_add_column(
    table_ref: TableReference,
    col_name: str,
    *,
    read_version: int | None = None,
    concurrency: int = 8,
    batch_size: int | None = None,
    task_shuffle_diversity: int | None = None,
    commit_granularity: int | None = None,
    where: str | None = None,
    **kwargs,
) -> JobFuture:
    """
    Dispatch the Ray add column operation to a remote function.
    This is a convenience function to allow calling the remote function directly.
    """
    from datetime import datetime

    from geneva._context import get_current_context
    from geneva.manifest.mgr import ManifestConfigManager
    from geneva.utils import current_user

    db = table_ref.open_db()
    hist = db._history

    # Extract manifest info from current context
    manifest_id = None
    manifest_checksum = None
    ctx = get_current_context()
    if ctx is not None and ctx.manifest is not None:
        manifest = ctx.manifest
        manifest_checksum = manifest.checksum

        # Auto-register manifest if not already persisted
        if not manifest.name:
            # Generate auto name
            user = current_user()
            timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            checksum_short = manifest.checksum[:8] if manifest.checksum else "unknown"
            manifest.name = f"auto-{user}-{timestamp}-{checksum_short}"
            _LOG.info(f"Auto-registering manifest as '{manifest.name}'")

        manifest_id = manifest.name

        # Ensure manifest is registered in the database
        manifest_mgr = ManifestConfigManager(db)
        existing = manifest_mgr.load(manifest.name)
        if existing is None:
            _LOG.info(f"Upserting manifest '{manifest.name}' to database")
            manifest_mgr.upsert(manifest)

    job = hist.launch(
        table_ref.table_name,
        col_name,
        where=where,
        manifest_id=manifest_id,
        manifest_checksum=manifest_checksum,
        **kwargs,
    )

    job_tracker = JobTracker.options(
        name=f"jobtracker-{job.job_id}",
        num_cpus=0.1,
        memory=128 * 1024 * 1024,
        max_restarts=-1,
    ).remote(job.job_id)

    obj_ref = run_ray_add_column_remote.remote(  # type: ignore[call-arg,misc]
        table_ref,
        col_name,
        read_version=read_version,  # type: ignore[call-arg]
        job_id=job.job_id,  # type: ignore[call-arg]
        job_tracker=job_tracker,  # type: ignore[call-arg]
        concurrency=concurrency,  # type: ignore[call-arg]
        batch_size=batch_size,  # type: ignore[call-arg]
        task_shuffle_diversity=task_shuffle_diversity,  # type: ignore[call-arg]
        commit_granularity=commit_granularity,  # type: ignore[call-arg]
        where=where,  # type: ignore[call-arg]
        **kwargs,
    )
    # object ref is only available here
    hist.set_object_ref(job.job_id, cloudpickle.dumps(obj_ref))
    return RayJobFuture(
        job_id=job.job_id,
        ray_obj_ref=obj_ref,
        job_tracker=job_tracker,  # type: ignore[arg-type]
    )


def validate_backfill_args(
    tbl: Table,
    col_name: str,
    udf: UDF | None = None,
    input_columns: list[str] | None = None,
) -> None:
    """
    Validate the arguments for the backfill operation.

    This function performs validation before starting a backfill job to catch
    configuration errors early. It validates:

    1. Target column exists in the table
    2. UDF input columns exist in table schema
    3. Column types are compatible with UDF type annotations (if present)

    All validation is delegated to UDF.validate_against_schema() for consistency.

    Parameters
    ----------
    tbl : Table
        The table to backfill
    col_name : str
        The column name to backfill
    udf : UDF | None
        The UDF to use (if None, will be loaded from column metadata)
    input_columns : list[str] | None
        The input columns for the UDF (if None, will be loaded from column metadata)

    Raises
    ------
    ValueError
        If validation fails (missing columns, type mismatches, etc.)

    Warns
    -----
    UserWarning
        If type validation is skipped due to missing type annotations
    """
    if col_name not in tbl._ltbl.schema.names:
        raise ValueError(
            f"Column {col_name} is not defined this table.  "
            "Use add_columns to register it first"
        )

    if udf is None:
        udf_spec = fetch_udf(tbl, col_name)
        udf = tbl._conn._packager.unmarshal(udf_spec)

    # Get input_columns from column metadata if not provided
    if input_columns is None:
        field = tbl._ltbl.schema.field(col_name)
        metadata = field.metadata or {}
        input_columns = json.loads(metadata.get(b"virtual_column.udf_inputs", "null"))

    # Delegate to UDF's consolidated validation method
    udf.validate_against_schema(tbl._ltbl.schema, input_columns)


@ray.remote
def run_ray_add_column_remote(
    table_ref: TableReference,
    col_name: str,
    *,
    job_id: str | None = None,
    udf: UDF | None = None,
    read_version: int | None = None,
    concurrency: int = 8,
    batch_size: int | None = None,
    task_shuffle_diversity: int | None = None,
    commit_granularity: int | None = None,
    where: str | None = None,
    job_tracker: ActorHandle | None = None,
    **kwargs,
) -> None:
    """
    Remote function to run the Ray add column operation.
    This is a wrapper around `run_ray_add_column` to allow it to be called as a Ray
    task.
    """
    import geneva  # noqa: F401  Force so that we have the same env in next level down

    tbl = table_ref.open()
    hist = tbl._conn._history
    if job_id:
        hist.set_running(job_id)
    try:
        # Get input_columns from column metadata first
        field = tbl._ltbl.schema.field(col_name)
        metadata = field.metadata or {}
        input_columns = json.loads(metadata.get(b"virtual_column.udf_inputs", "null"))

        validate_backfill_args(tbl, col_name, udf, input_columns)
        if udf is None:
            udf_spec = fetch_udf(tbl, col_name)
            udf = tbl._conn._packager.unmarshal(udf_spec)

        # Apply input_columns override to the UDF if needed
        # This handles the case where add_columns was called with explicit column
        # mapping e.g., table.add_columns({"col": (udf, ["seq"])})
        if input_columns is not None and udf.input_columns != input_columns:
            udf.input_columns = input_columns

        from geneva.runners.ray.pipeline import run_ray_add_column

        checkpoint_store = tbl._conn._checkpoint_store
        run_ray_add_column(
            table_ref,
            input_columns,
            {col_name: udf},
            checkpoint_store=checkpoint_store,
            read_version=read_version,
            job_id=job_id,
            concurrency=concurrency,
            batch_size=batch_size,
            task_shuffle_diversity=task_shuffle_diversity,
            commit_granularity=commit_granularity,
            where=where,
            job_tracker=job_tracker,
            **kwargs,
        )
        if job_id:
            hist.set_completed(job_id)
    except Exception as e:
        _LOG.exception("Error running Ray add column operation")
        if job_id:
            hist.set_failed(job_id, str(e))
        raise e


def run_ray_add_column(
    table_ref: TableReference,
    columns: list[str] | None,
    transforms: dict[str, UDF],
    checkpoint_store: CheckpointStore | None = None,
    *,
    read_version: int | None = None,
    job_id: str | None = None,
    concurrency: int = 8,
    batch_size: int | None = None,
    task_shuffle_diversity: int | None = None,
    commit_granularity: int | None = None,
    where: str | None = None,
    job_tracker=None,
    **kwargs,
) -> None:
    # prepare job parameters
    config = JobConfig.get().with_overrides(
        batch_size=batch_size,
        task_shuffle_diversity=task_shuffle_diversity,
        commit_granularity=commit_granularity,
    )

    checkpoint_store = checkpoint_store or config.make_checkpoint_store()

    table = table_ref.open()
    uri = table.to_lance().uri

    # add pre-existing col if carrying previous values forward
    carry_forward_cols = list(set(transforms.keys()) & set(table.schema.names))
    _LOG.debug(f"carry_forward_cols {carry_forward_cols}")
    # this copy is necessary because the array extending updates inplace and this
    # columns array is directly referenced by the udf instance earlier
    cols = table.schema.names.copy() if columns is None else columns.copy()
    for cfcol in carry_forward_cols:
        # only append if cf col is not in col list already
        if cfcol not in cols:
            cols.append(cfcol)

    map_task = BackfillUDFTask(udfs=transforms, where=where)

    plan, pipeline_args = plan_read(
        uri,
        cols,
        batch_size=config.batch_size,
        read_version=read_version,
        task_shuffle_diversity=config.task_shuffle_diversity,
        where=where,
        map_task=map_task,
        checkpoint_store=checkpoint_store,
        **kwargs,
    )

    _LOG.info(
        f"starting backfill pipeline for {transforms} where='{where}'"
        f" with carry_forward_cols={carry_forward_cols}"
    )
    _run_column_adding_pipeline(
        map_task,
        checkpoint_store,
        config,
        table_ref,
        plan,
        job_id,
        concurrency,
        where=where,
        job_tracker=job_tracker,
        **pipeline_args,
    )


@attrs.define
class RayJobFuture(JobFuture):
    ray_obj_ref: ActorHandle = attrs.field()
    job_tracker: ActorHandle | None = attrs.field(default=None)
    _pbars: dict[str, TqdmType] = attrs.field(factory=dict)
    _RAY_LINE_KEY: str = "_ray_summary_line"

    def _sync_bars(self, snapshot: dict[str, dict]) -> None:
        # single line ray summary
        wa = snapshot.get(CNT_WORKERS_ACTIVE)
        wp = snapshot.get(CNT_WORKERS_PENDING)
        if wa or wp:
            bar = self._pbars.get(self._RAY_LINE_KEY)
            if bar is None:
                # text-only line, like k8s/kr bars
                bar = tqdm(total=0, bar_format="{desc} {bar:0}[{elapsed}]")
                self._pbars[self._RAY_LINE_KEY] = bar

            def _fmt(m: dict[str, Any] | None) -> str:
                if not m:
                    return "?"
                n = m.get("n", 0)
                return f"{n}"

            bar.desc = f"geneva | workers (active/pending): {_fmt(wa)}/{_fmt(wp)}"
            bar.refresh()

            # close when all are done (harmless if left open)
            if all(m and m.get("done") for m in (wa, wp)):
                bar.close()

        for name, m in snapshot.items():
            if name in {
                CNT_RAY_NODES,
                CNT_WORKERS_PENDING,
                CNT_WORKERS_ACTIVE,
            }:
                continue

            n, total, done, desc = m["n"], m["total"], m["done"], m.get("desc", name)
            bar = self._pbars.get(name)
            if bar is None:
                # Only make bars for the known core metrics (skip "fragments",
                # "writer_fragments", and other randoms)
                if name not in {
                    "rows_checkpointed",
                    "rows_ready_for_commit",
                    "rows_committed",
                }:
                    continue
                bar = tqdm(total=total, desc=desc)
                self._pbars[name] = bar
            bar.total = total
            bar.n = n
            bar.refresh()
            if done:
                bar.close()

    def status(self) -> None:
        if self.job_tracker is None:
            return
        try:
            snapshot = ray.get(self.job_tracker.get_all.remote(), timeout=0.05)
            self._sync_bars(snapshot)  # type: ignore[arg-type]
        except ray.exceptions.GetTimeoutError:
            _LOG.debug("JobTracker not ready? skip this tick")
            return

    def done(self, timeout: float = 0.0) -> bool:
        self.status()
        _LOG.debug("Waiting for Ray job %s to complete", self.ray_obj_ref)
        ready, _ = ray.wait([self.ray_obj_ref], timeout=timeout)
        _LOG.debug("Ray jobs ready %s to complete", ready)
        done = bool(ready)
        if done:
            self.status()
        return done

    def result(self, timeout: float | None = None) -> Any:
        # TODO this can throw a ray.exceptions.GetTimeoutError if the task
        # does not complete in time, we should create a new exception type to
        # encapsulate Ray specifics
        self.status()
        return ray.get(self.ray_obj_ref, timeout=timeout)  # type: ignore[call-overload,arg-type]


def get_imported_packages() -> dict:
    import importlib
    import sys

    packages = {}
    for name, module in sys.modules.items():
        if module is None:
            continue
        try:
            mod = importlib.import_module(name.split(".")[0])
            version = getattr(mod, "__version__", None)
            if version:
                packages[mod.__name__] = version
        except Exception as e:
            _LOG.error(e)
            continue
    return packages


@ray.remote
def get_imported() -> dict:
    """A simple utility to return the names and versions of python packages
    installed in the current Ray worker environment."""
    return get_imported_packages()
