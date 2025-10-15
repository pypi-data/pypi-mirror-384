# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright The Geneva Authors

import itertools
import logging
import random
from collections.abc import Callable, Iterator, Mapping
from typing import TypeVar

import attrs
import lance
import more_itertools
import pyarrow as pa
from yarl import URL

from geneva.apply.applier import BatchApplier
from geneva.apply.simple import SimpleApplier
from geneva.apply.task import (
    DEFAULT_CHECKPOINT_ROWS,
    CopyTask,
    MapTask,
    ReadTask,
    ScanTask,
)
from geneva.checkpoint import CheckpointStore
from geneva.debug.logger import ErrorLogger, NoOpErrorLogger
from geneva.table import TableReference

_LOG = logging.getLogger(__name__)


def _check_fragment_data_file_exists(
    uri: str,
    frag_id: int,
    map_task: MapTask,
    checkpoint_store: CheckpointStore,
) -> bool:
    """
    Check if a fragment data file already exists in staging or target locations.

    Returns True if the fragment can be skipped because its data file already exists.
    """
    # Import here to avoid circular imports
    from geneva.runners.ray.pipeline import _get_fragment_dedupe_key

    # Get the fragment's checkpoint key
    dedupe_key = _get_fragment_dedupe_key(uri, frag_id, map_task)

    # Check if fragment is already checkpointed
    if dedupe_key not in checkpoint_store:
        return False

    try:
        # Get the stored file path from checkpoint
        checkpointed_data = checkpoint_store[dedupe_key]
        if "file" not in checkpointed_data.schema.names:
            return False

        file_list = checkpointed_data["file"].to_pylist()
        file_path = "".join(str(f) for f in file_list if f is not None)
        if not file_path:
            return False

        # Check staging location first (dataset/data/{file}.lance)
        base_url = URL(uri)
        if base_url.scheme == "":
            base_url = URL(f"file://{uri}")

        # For Lance datasets, the URI ends with .lance, get the parent directory
        if str(base_url).endswith(".lance"):
            base_url = base_url.parent

        staging_url = base_url / "data" / file_path

        try:
            # Check if the staging file exists using lance's file system abstraction
            from pyarrow.fs import FileSystem

            fs, path = FileSystem.from_uri(str(staging_url))
            file_info = fs.get_file_info(path)
            from pyarrow.fs import FileType

            if file_info.type != FileType.NotFound:
                _LOG.info(
                    f"Fragment {frag_id} data file exists in staging: {staging_url}"
                )
                return True
        except Exception as e:
            _LOG.debug(f"Failed to check staging location {staging_url}: {e}")

        # Check target table location as fallback
        # The file might have been moved/committed to the main dataset
        dataset = lance.dataset(uri)
        try:
            fragment = dataset.get_fragment(frag_id)
            if fragment is not None:
                # Check if any data files in the fragment match our expected file
                for data_file in fragment.data_files():
                    if data_file.path == file_path:
                        _LOG.info(
                            f"Fragment {frag_id} data file exists in target: "
                            f"{data_file.path}"
                        )
                        return True
        except Exception as e:
            _LOG.debug(f"Failed to check target location for fragment {frag_id}: {e}")

    except Exception as e:
        _LOG.debug(f"Failed to check fragment data file for {frag_id}: {e}")

    return False


@attrs.define
class CheckpointingApplier:
    """
    Reads a read task and applies a map task to the data
    using a batch applier.

    The applier will checkpoint the output of the map task so that it can be
    resumed from the same point if the job is interrupted.
    """

    checkpoint_uri: str = attrs.field()
    map_task: MapTask = attrs.field()

    error_logger: ErrorLogger = attrs.field(default=NoOpErrorLogger())
    batch_applier: BatchApplier = attrs.field(
        factory=SimpleApplier,
        converter=attrs.converters.default_if_none(factory=SimpleApplier),
    )

    checkpoint_store: CheckpointStore = attrs.field(init=False)

    def __attrs_post_init__(self) -> None:
        self.checkpoint_store = CheckpointStore.from_uri(self.checkpoint_uri)

    @property
    def output_schema(self) -> pa.Schema:
        return self.map_task.output_schema()

    def _run(self, task: ReadTask) -> str:
        data_key = task.checkpoint_key()
        _LOG.info("Running task %s", task)
        # track the batch sequence number so we can checkpoint any errors
        # when reproducing locally we can seek to the erroring batch quickly

        checkpoint_key = f"{data_key}:{self.map_task.checkpoint_key()}"
        if checkpoint_key in self.checkpoint_store:
            _LOG.info("Using cached result for %s", checkpoint_key)
            return checkpoint_key

        batch = self.batch_applier.run(
            task,
            self.map_task,
            error_logger=self.error_logger,
        )

        self.checkpoint_store[checkpoint_key] = batch
        _LOG.info(f"checkpointed key={checkpoint_key}")
        return checkpoint_key

    def run(self, task: ReadTask) -> str:
        try:
            return self._run(task)
        except Exception as e:
            logging.exception("Error running task %s: %s", task, e)
            raise RuntimeError(f"Error running task {task}") from e

    def status(self, task: ReadTask) -> bool:
        data_key = task.checkpoint_key()
        return f"{data_key}:{self.map_task.checkpoint_key()}" in self.checkpoint_store


def _plan_read(
    uri: str,
    columns: list[str],
    *,
    read_version: int | None = None,
    batch_size: int = DEFAULT_CHECKPOINT_ROWS,
    where: str | None = None,
    num_frags: int | None = None,
    map_task: MapTask | None = None,
    checkpoint_store: CheckpointStore | None = None,
) -> tuple[Iterator[ReadTask], dict, dict]:
    """Make Plan for Reading Data from a Dataset
    We want a ScanTask for each fragment in the dataset even if they are filtered
    out. This should make the checkpointing recovery easier to manage.

    Returns a tuple of (ReadTask iterator, skipped_fragments dict, skipped_stats dict).
    skipped_stats contains {'fragments': count, 'rows': count} for progress tracking.
    """
    dataset = lance.dataset(uri)
    if read_version is not None:
        dataset = dataset.checkout_version(read_version)

    skipped_fragments = {}
    skipped_stats = {"fragments": 0, "rows": 0}
    tasks = []

    # get_fragments has an unsupported filter method, so we do filtering deeper in.
    for idx, frag in enumerate(dataset.get_fragments()):
        _LOG.info(
            f"Processing fragment {idx} (fragment_id={frag.fragment_id}), "
            f"num_frags={num_frags}"
        )
        if num_frags is not None and idx >= num_frags:
            _LOG.info(f"Breaking loop: idx {idx} >= num_frags {num_frags}")
            break

        # Check if fragment data file already exists (fragment-level checkpoint)
        checkpoint_exists = (
            map_task is not None
            and checkpoint_store is not None
            and _check_fragment_data_file_exists(
                uri, frag.fragment_id, map_task, checkpoint_store
            )
        )
        _LOG.info(
            f"Fragment {idx} (fragment_id={frag.fragment_id}): "
            f"checkpoint_exists={checkpoint_exists}"
        )

        if checkpoint_exists:
            _LOG.info(
                f"Skipping fragment {frag.fragment_id} - data file already exists"
            )

            # Count rows in skipped fragment for progress tracking
            frag_rows = frag.count_rows()
            filtered_frag_rows = frag.count_rows(filter=where)
            skipped_rows = filtered_frag_rows if where else frag_rows

            skipped_stats["fragments"] += 1
            skipped_stats["rows"] += skipped_rows

            # Collect skipped fragment information for commit inclusion
            from geneva.runners.ray.pipeline import _get_fragment_dedupe_key
            from geneva.utils.parse_rust_debug import extract_field_ids

            # These should not be None here due to the checkpoint_exists check above
            assert map_task is not None
            assert checkpoint_store is not None

            dedupe_key = _get_fragment_dedupe_key(uri, frag.fragment_id, map_task)
            checkpointed_data = checkpoint_store[dedupe_key]
            file_list = checkpointed_data["file"].to_pylist()
            file_path = "".join(str(f) for f in file_list if f is not None)

            # The checkpointed files should only contain the columns being transformed
            # For UDF tasks, determine the field_ids for the output columns
            # Use the same logic as the writer to ensure consistency
            field_ids = []
            if hasattr(map_task, "udfs") and map_task.udfs:  # type: ignore[attr-defined]
                # Use extract_field_ids for consistency with writer.py
                # Pre-check schema to avoid try-except in loop (PERF203)
                schema_fields = {
                    field.name() for field in dataset.lance_schema.fields()
                }

                for column_name in map_task.udfs:  # type: ignore[attr-defined]
                    if column_name not in schema_fields:
                        # Column doesn't exist in current schema, this shouldn't happen
                        # for checkpointed fragments, but if it does, skip this fragment
                        _LOG.warning(
                            f"Column {column_name} not found in schema for "
                            f"checkpointed fragment {frag.fragment_id}, skipping"
                        )
                        continue

                    field_ids.extend(
                        extract_field_ids(dataset.lance_schema, column_name)
                    )
            else:
                # Fallback: use all columns (this shouldn't happen for UDF tasks)
                for column_name in columns:
                    field_ids.extend(
                        extract_field_ids(dataset.lance_schema, column_name)
                    )

            # Create a DataFile object for this existing file
            existing_data_file = lance.fragment.DataFile(
                file_path,
                field_ids,
                list(range(len(field_ids))),
                2,  # major_version
                0,  # minor_version
            )
            skipped_fragments[frag.fragment_id] = existing_data_file
            continue

        frag_rows = frag.count_rows()
        filtered_frag_rows = frag.count_rows(filter=where)
        if filtered_frag_rows == 0:
            _LOG.debug(
                f"frag {frag.fragment_id} filtered by '{where}' has no rows, skipping."
            )
            continue

        _LOG.debug(
            f"plan_read fragment: {frag} has {frag_rows} rows, filtered to"
            f" {filtered_frag_rows} rows"
        )
        for offset in range(0, frag_rows, batch_size if batch_size > 0 else frag_rows):
            limit = min(batch_size, frag_rows - offset)
            _LOG.debug(
                f"scan task: idx={idx} fragid={frag.fragment_id} offset={offset} "
                f"limit={limit} where={where}"
            )
            tasks.append(
                ScanTask(
                    uri=uri,
                    version=read_version,
                    columns=columns,
                    frag_id=frag.fragment_id,
                    offset=offset,
                    limit=limit,
                    where=where,
                    with_row_address=True,
                )
            )

    return iter(tasks), skipped_fragments, skipped_stats


T = TypeVar("T")  # Define type variable "T"


@attrs.define
class _LanceReadPlanIterator(Iterator[T]):
    it: Iterator[T]
    total: int

    def __iter__(self) -> Iterator[T]:
        return self

    def __next__(self) -> T:
        return next(self.it)

    def __len__(self) -> int:
        return self.total


def _num_tasks(
    *,
    uri: str,
    read_version: int | None = None,
    batch_size: int = DEFAULT_CHECKPOINT_ROWS,
) -> int:
    if batch_size <= 0:
        return 1
    return sum(
        -(-frag.count_rows() // batch_size)
        for frag in (lance.dataset(uri, version=read_version)).get_fragments()
    )


T = TypeVar("T")


def _buffered_shuffle(it: Iterator[T], buffer_size: int) -> Iterator[T]:
    """Shuffle an iterator using a buffer of size buffer_size
    not perfectly random, but good enough for spreading out IO
    """
    # Initialize the buffer with the first buffer_size items from the iterator
    buffer = []
    # Fill the buffer with up to buffer_size items initially
    try:
        for _ in range(buffer_size):
            item = next(it)
            buffer.append(item)
    except StopIteration:
        pass

    while True:
        # Select a random item from the buffer
        index = random.randint(0, len(buffer) - 1)
        item = buffer[index]

        # Try to replace the selected item with a new one from the iterator
        try:
            next_item = next(it)
            buffer[index] = next_item
            # Yield the item AFTER replacing it in the buffer
            # this way the buffer is always contiguous so we can
            # simply yield the buffer at the end
            yield item
        except StopIteration:
            yield from buffer
            break


R = TypeVar("R")


def diversity_aware_shuffle(
    it: Iterator[T],
    key: Callable[[T], R],
    *,
    diversity_goal: int = 4,
    buffer_size: int = 1024,
) -> Iterator[T]:
    """A shuffle iterator that is aware of the diversity of the data
    being shuffled. The key function should return a value that is
    is used to determine the diversity of the data. The diversity_goal
    is the number of unique values that should be in the buffer at any
    given time. if the buffer is full, the items is yielded in a round-robin
    fashion. This is useful for shuffling tasks that are diverse, but

    This algorithm is bounded in memory by the buffer_size, so it is reasonably
    efficient for large datasets.
    """

    # NOTE: this is similar to itertools.groupby, but with a buffering limit

    buffer: dict[R, list[T]] = {}
    buffer_total_size = 0

    peekable_it = more_itertools.peekable(it)

    def _maybe_consume_from_iter() -> bool:
        nonlocal buffer_total_size
        item = peekable_it.peek(default=None)
        if item is None:
            return False
        key_val = key(item)
        if key_val not in buffer and len(buffer) < diversity_goal:
            buffer[key_val] = []
        else:
            return False

        # if the buffer still has room, add the item
        if buffer_total_size < buffer_size:
            buffer[key_val].append(item)
            buffer_total_size += 1
        else:
            return False

        next(peekable_it)
        return True

    while _maybe_consume_from_iter():
        ...

    production_counter = 0

    def _next_key() -> T | None:
        nonlocal buffer_total_size, production_counter
        if not buffer_total_size:
            return None

        # TODO: add warning about buffer size not big enough for diversity_goal
        buffer_slot = production_counter % len(buffer)
        key = next(itertools.islice(buffer.keys(), buffer_slot, buffer_slot + 1))
        assert key in buffer
        key_buffer = buffer[key]

        buffer_total_size -= 1
        item = key_buffer.pop(0)
        if not key_buffer:
            del buffer[key]

        # try to fill the removed buffer slot
        _maybe_consume_from_iter()
        production_counter += 1
        return item

    while (item := _next_key()) is not None:
        yield item


def plan_read(
    uri: str,
    columns: list[str],
    *,
    read_version: int | None = None,
    batch_size: int = DEFAULT_CHECKPOINT_ROWS,
    where: str | None = None,
    shuffle_buffer_size: int = 0,
    task_shuffle_diversity: int | None = None,
    num_frags: int | None = None,
    map_task: MapTask | None = None,
    checkpoint_store: CheckpointStore | None = None,
    **unused_kwargs,
) -> tuple[Iterator[ReadTask], Mapping]:
    """
    Make Plan for Reading Data from a Dataset

    Parameters
    ----------
    num_frags:
        max number of fragments to scan for sampling use cases.
    """
    it, skipped_fragments, skipped_stats = _plan_read(
        uri,
        columns=columns,
        read_version=read_version,
        batch_size=batch_size,
        where=where,
        num_frags=num_frags,
        map_task=map_task,
        checkpoint_store=checkpoint_store,
    )
    # same as no shuffle
    if shuffle_buffer_size > 1 and task_shuffle_diversity is None:
        it = _buffered_shuffle(it, buffer_size=shuffle_buffer_size)
    elif task_shuffle_diversity is not None:
        buffer_size = max(4 * task_shuffle_diversity, shuffle_buffer_size)
        it = diversity_aware_shuffle(
            it,
            key=lambda task: task.checkpoint_key(),
            diversity_goal=task_shuffle_diversity,
            buffer_size=buffer_size,
        )

    unused_kwargs["skipped_fragments"] = skipped_fragments
    unused_kwargs["skipped_stats"] = skipped_stats

    return _LanceReadPlanIterator(
        it, _num_tasks(uri=uri, read_version=read_version, batch_size=batch_size)
    ), unused_kwargs


def _plan_copy(
    src: TableReference,
    dst: TableReference,
    columns: list[str],
    *,
    batch_size: int = DEFAULT_CHECKPOINT_ROWS,
) -> tuple[Iterator[CopyTask], int]:
    """Make Plan for Reading Data from a Dataset"""
    dst_dataset = dst.open().to_lance()
    num_tasks = 0
    for frag in dst_dataset.get_fragments():
        frag_rows = frag.count_rows()
        # ceil_div
        num_tasks += -(frag_rows // -batch_size)

    def task_gen() -> Iterator[CopyTask]:
        for frag in dst_dataset.get_fragments():
            frag_rows = frag.count_rows()
            for offset in range(0, frag_rows, batch_size):
                limit = min(batch_size, frag_rows - offset)
                yield CopyTask(
                    src=src,
                    dst=dst,
                    columns=columns,
                    frag_id=frag.fragment_id,
                    offset=offset,
                    limit=limit,
                )

    return (task_gen(), num_tasks)


def plan_copy(
    src: TableReference,
    dst: TableReference,
    columns: list[str],
    *,
    batch_size: int = DEFAULT_CHECKPOINT_ROWS,
    shuffle_buffer_size: int = 0,
    task_shuffle_diversity: int | None = None,
) -> Iterator[CopyTask]:
    (it, num_tasks) = _plan_copy(
        src,
        dst,
        columns,
        batch_size=batch_size,
    )
    # same as no shuffle
    if shuffle_buffer_size > 1 and task_shuffle_diversity is None:
        it = _buffered_shuffle(it, buffer_size=shuffle_buffer_size)
    elif task_shuffle_diversity is not None:
        buffer_size = max(4 * task_shuffle_diversity, shuffle_buffer_size)
        it = diversity_aware_shuffle(
            it,
            key=lambda task: task.checkpoint_key(),
            diversity_goal=task_shuffle_diversity,
            buffer_size=buffer_size,
        )

    return _LanceReadPlanIterator(it, num_tasks)
