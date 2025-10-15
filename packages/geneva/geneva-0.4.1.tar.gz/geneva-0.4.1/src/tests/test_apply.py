# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright The Geneva Authors

import logging
from pathlib import Path

import lance
import pyarrow as pa
import pyarrow.compute as pc
import pytest
from yarl import URL

from geneva import CheckpointStore, connect, udf
from geneva.apply import (
    CheckpointingApplier,
    _check_fragment_data_file_exists,
    plan_read,
)
from geneva.apply.task import BackfillUDFTask
from geneva.debug.logger import CheckpointStoreErrorLogger
from geneva.runners.ray.pipeline import FragmentWriterManager, _get_fragment_dedupe_key

_LOG = logging.getLogger(__name__)


def test_create_plan(tmp_path: Path) -> None:
    db = connect(tmp_path)
    tbl = db.create_table("tbl", pa.table({"a": [1, 2, 3]}))

    plans = list(plan_read(tbl.uri, ["a"], batch_size=16)[0])
    assert len(plans) == 1
    plan = plans[0]
    assert plan.uri == tbl.uri
    assert plan.offset == 0
    assert plan.limit == 3


def test_create_plan_with_diverse_shuffle(tmp_path: Path) -> None:
    ds = lance.write_dataset(
        pa.table({"a": range(1024)}), tmp_path / "tbl", max_rows_per_file=16
    )

    plans = list(plan_read(ds.uri, ["a"], batch_size=1, task_shuffle_diversity=4)[0])
    assert len(plans) == 1024
    plan = plans[0]
    assert plan.uri == ds.uri
    assert plan.offset == 0
    assert plan.limit == 1


@udf(input_columns=["a"])
def one(*args, **kwargs) -> int:
    return 1


def test_applier(tmp_path: Path) -> None:
    db = connect(tmp_path)
    tbl = db.create_table("tbl", pa.table({"a": [1, 2, 3]}))

    plans = list(plan_read(tbl.uri, ["a"], batch_size=16)[0])
    assert len(plans) == 1
    plan = plans[0]
    assert plan.uri == tbl.uri
    assert plan.offset == 0
    assert plan.limit == 3

    store = CheckpointStore.from_uri(str(URL(str(tmp_path)) / "ckp"))
    applier = CheckpointingApplier(
        map_task=BackfillUDFTask(udfs={"one": one}),
        checkpoint_uri=store.root,
    )
    key = applier.run(plan)
    batch = store[key]
    assert len(batch) == 3
    assert batch.to_pydict() == {"one": [1, 1, 1], "_rowaddr": [0, 1, 2]}


def test_applier_with_where(tmp_path: Path) -> None:
    db = connect(tmp_path)
    tbl = db.create_table("tbl", pa.table({"a": [1, 2, 3, 4, 5, 6, 7, 8]}))

    plans = list(plan_read(tbl.uri, ["a"], batch_size=3, where="a%2=0")[0])

    assert len(plans) == 3  # 1-3, 4-6, and 7-8
    plan = plans[0]
    assert plan.uri == tbl.uri
    assert plan.offset == 0
    assert plan.limit == 3

    store = CheckpointStore.from_uri(str(URL(str(tmp_path)) / "ckp"))
    applier = CheckpointingApplier(
        map_task=BackfillUDFTask(udfs={"one": one}),
        checkpoint_uri=store.root,
    )

    # Lance forces us to eithe write the entire column or write an entire row.  This
    # applier writes the whole col.  So we actually do all the scans and filter at udf
    # execution time.  When the udf is not executed we return None.

    expected = [
        {"one": [None, 1, None], "_rowaddr": [0, 1, 2]},
        {"one": [1, None, 1], "_rowaddr": [3, 4, 5]},
        {"one": [None, 1], "_rowaddr": [6, 7]},
    ]

    for i, plan in enumerate(plans):
        key = applier.run(plan)
        batch = store[key]
        assert batch.to_pydict() == expected[i]


def test_applier_with_where2(tmp_path: Path) -> None:
    db = connect(tmp_path)
    tbl = db.create_table("tbl", pa.table({"a": [1, 2, 3, 4, 5, 6, 7, 8]}))

    plans = list(plan_read(tbl.uri, ["a"], batch_size=1, where="a%2=0")[0])

    assert len(plans) == 8  # 1-3, 4-6, and 7-8
    plan = plans[0]
    assert plan.uri == tbl.uri
    assert plan.offset == 0
    assert plan.limit == 1

    store = CheckpointStore.from_uri(str(URL(str(tmp_path)) / "ckp"))
    applier = CheckpointingApplier(
        map_task=BackfillUDFTask(udfs={"one": one}),
        checkpoint_uri=store.root,
    )

    expected = [
        {"one": [None], "_rowaddr": [0]},
        {"one": [1], "_rowaddr": [1]},
        {"one": [None], "_rowaddr": [2]},
        {"one": [1], "_rowaddr": [3]},
        {"one": [None], "_rowaddr": [4]},
        {"one": [1], "_rowaddr": [5]},
        {"one": [None], "_rowaddr": [6]},
        {"one": [1], "_rowaddr": [7]},
    ]

    for i, plan in enumerate(plans):
        key = applier.run(plan)
        batch = store[key]
        assert batch.to_pydict() == expected[i]


def test_applier_with_incremental(tmp_path: Path) -> None:
    db = connect(tmp_path)
    tbl = db.create_table(
        "tbl",
        pa.table(
            {
                "a": [1, 2, 3, 4, 5, 6, 7, 8],
                "one": [
                    None,
                    1,
                    None,
                    1,
                    None,
                    1,
                    None,
                    1,
                ],
            }
        ),
    )

    # apply a update plan that covers the rest
    plans = list(
        plan_read(
            tbl.uri,
            ["a", "one"],  # input col and carry forward the output cols
            batch_size=1,
            carry_forward_cols=["one"],
            where="one is Null",
        )[0]
    )
    _LOG.debug(plans)

    store = CheckpointStore.from_uri(str(URL(str(tmp_path)) / "ckp"))
    applier = CheckpointingApplier(
        map_task=BackfillUDFTask(udfs={"one": one}),
        checkpoint_uri=store.root,
    )

    expected = [
        {"one": [1], "_rowaddr": [0]},
        {"one": [1], "_rowaddr": [1]},
        {"one": [1], "_rowaddr": [2]},
        {"one": [1], "_rowaddr": [3]},
        {"one": [1], "_rowaddr": [4]},
        {"one": [1], "_rowaddr": [5]},
        {"one": [1], "_rowaddr": [6]},
        {"one": [1], "_rowaddr": [7]},
    ]

    for i, plan in enumerate(plans):
        key = applier.run(plan)
        batch = store[key]
        assert batch.to_pydict() == expected[i]


@udf()
def errors_on_three(a: int) -> int:
    if a == 3:
        raise ValueError("This is an error")
    return 1


@pytest.mark.xfail(
    reason="new LanceSessionizedCheckpointStore escapes '/' while while "
    "legacy LanceCheckpointStore does not"
)
def test_applier_error_logging(tmp_path: Path) -> None:
    db = connect(tmp_path)
    tbl = db.create_table("tbl", pa.table({"a": [1, 2, 3]}))

    plans = list(plan_read(tbl.uri, ["a"], batch_size=16)[0])
    assert len(plans) == 1
    plan = plans[0]
    assert plan.uri == tbl.uri
    assert plan.offset == 0
    assert plan.limit == 3

    store = CheckpointStore.from_uri(str(URL(str(tmp_path)) / "ckp"))
    error_logger = CheckpointStoreErrorLogger("job_id", store)
    applier = CheckpointingApplier(
        map_task=BackfillUDFTask(udfs={"one": errors_on_three}),
        checkpoint_uri=store.root,
        error_logger=error_logger,
    )
    with pytest.raises(RuntimeError):
        applier.run(plan)

    assert len(list(error_logger.list_errors())) == 1
    error_id = list(error_logger.list_errors())[0]
    error = error_logger.get_error_row(error_id).to_pylist()[0]
    assert error["error"] == "This is an error"
    assert error["seq"] == 0


def test_plan_with_where(tmp_path: Path) -> None:
    db = connect(tmp_path)

    tbl = db.create_table("t", pa.table({"a": range(100)}))
    tbl.add(pa.table({"a": range(100, 200)}))
    tbl.add(pa.table({"a": range(200, 300)}))
    tbl.add(pa.table({"a": range(300, 400)}))

    fragments = tbl.get_fragments()
    assert len(fragments) == 4

    # even though we have a filter, we still have to read all the fragments
    # batch size 0 means one task per  fragment
    tasks = list(
        plan_read(tbl.uri, ["a"], where="a > 100 AND a % 2 == 0", batch_size=0)[0]
    )
    # there are only 3 tasks because we skip the first fragment due to the where clause.
    assert len(tasks) == 3


def test_plan_with_row_address(tmp_path: Path) -> None:
    db = connect(tmp_path)

    tbl = db.create_table("t", pa.table({"a": range(100)}))

    fragments = tbl.get_fragments()
    assert len(fragments) == 1

    tasks = list(plan_read(tbl.uri, ["a"], batch_size=1000)[0])
    assert len(tasks) == 1

    for batch in tasks[0].to_batches():
        assert "_rowaddr" in batch.column_names


def test_plan_with_num_frags(tmp_path: Path) -> None:
    db = connect(tmp_path)

    tbl = db.create_table("t", pa.table({"a": range(100)}))
    tbl.add(pa.table({"a": range(100, 200)}))
    tbl.add(pa.table({"a": range(200, 300)}))
    tbl.add(pa.table({"a": range(300, 400)}))

    fragments = tbl.get_fragments()
    assert len(fragments) == 4

    # even though we have a filter, we still have to read all the fragments
    tasks = list(plan_read(tbl.uri, ["a"], num_frags=2)[0])
    # there are only 2 tasks because we set num_frags=2
    assert len(tasks) == 2


def test_udf_with_arrow_params(tmp_path: Path) -> None:
    @udf(data_type=pa.int32())
    def batch_udf(a: pa.Array, b: pa.Array) -> pa.Array:
        assert a == pa.array([1, 2, 3])
        assert b == pa.array([4, 5, 6])
        return pc.cast(pc.add(a, b), pa.int32())

    db = connect(tmp_path)
    tbl = db.create_table("t", pa.table({"a": [1, 2, 3], "b": [4, 5, 6]}))

    store = CheckpointStore.from_uri(str(URL(str(tmp_path)) / "ckp"))
    applier = CheckpointingApplier(
        map_task=BackfillUDFTask(udfs={"c": batch_udf}),
        checkpoint_uri=store.root,
    )
    key = applier.run(next(plan_read(tbl.uri, ["a", "b"], batch_size=16)[0]))
    batch = store[key]
    assert batch == pa.RecordBatch.from_pydict(
        {
            "c": pa.array([5, 7, 9], type=pa.int32()),
            "_rowaddr": pa.array([0, 1, 2], pa.uint64()),
        },
    )


def test_udf_with_arrow_struct(tmp_path: Path) -> None:
    struct_type = pa.struct([("rpad", pa.string()), ("lpad", pa.string())])

    @udf(data_type=struct_type)
    def struct_udf(a: pa.Array, b: pa.Array) -> pa.Array:
        assert a == pa.array([1, 2, 3])
        assert b == pa.array([4, 5, 6])
        rpad = pc.ascii_rpad(pc.cast(a, target_type="string"), 4, padding="0")
        lpad = pc.ascii_lpad(pc.cast(a, target_type="string"), 4, padding="0")
        return pc.make_struct(rpad, lpad, field_names=["rpad", "lpad"])

    db = connect(tmp_path)
    tbl = db.create_table("t", pa.table({"a": [1, 2, 3], "b": [4, 5, 6]}))

    store = CheckpointStore.from_uri(str(URL(str(tmp_path)) / "ckp"))
    applier = CheckpointingApplier(
        map_task=BackfillUDFTask(udfs={"c": struct_udf}),
        checkpoint_uri=store.root,
    )
    key = applier.run(next(plan_read(tbl.uri, ["a", "b"], batch_size=16)[0]))
    batch = store[key]
    # Build the expected RecordBatch
    # The function calls produce ["1000", "2000", "3000"] for rpad
    # and ["0001", "0002", "0003"] for lpad
    expected_batch = pa.RecordBatch.from_arrays(
        [
            pa.StructArray.from_arrays(
                [
                    pa.array(["1000", "2000", "3000"]),
                    pa.array(["0001", "0002", "0003"]),
                ],
                names=["rpad", "lpad"],
            ),
            pa.array([0, 1, 2], pa.uint64()),
        ],
        ["c", "_rowaddr"],
    )

    assert batch == expected_batch


def test_udf_with_arrow_array(tmp_path: Path) -> None:
    array_type = pa.list_(pa.int64())

    @udf(data_type=array_type)
    def array_udf(a: pa.Array, b: pa.Array) -> pa.Array:
        assert a == pa.array([1, 2, 3])
        assert b == pa.array([4, 5, 6])
        arr = [
            [val] * cnt for val, cnt in zip(a.to_pylist(), b.to_pylist(), strict=True)
        ]
        c = pa.array(arr, type=pa.list_(pa.int64()))
        return c

    db = connect(tmp_path)
    tbl = db.create_table("t", pa.table({"a": [1, 2, 3], "b": [4, 5, 6]}))

    store = CheckpointStore.from_uri(str(URL(str(tmp_path)) / "ckp"))
    applier = CheckpointingApplier(
        map_task=BackfillUDFTask(udfs={"c": array_udf}),
        checkpoint_uri=store.root,
    )
    key = applier.run(next(plan_read(tbl.uri, ["a", "b"], batch_size=16)[0]))
    batch = store[key]

    # Build the expected RecordBatch
    expected_c = pa.array(
        [[1, 1, 1, 1], [2, 2, 2, 2, 2], [3, 3, 3, 3, 3, 3]], type=pa.list_(pa.int64())
    )

    expected_batch = pa.RecordBatch.from_arrays(
        [expected_c, pa.array([0, 1, 2], pa.uint64())], ["c", "_rowaddr"]
    )
    assert batch == expected_batch


# Tests for fragment-level checkpoint functionality


def test_check_fragment_data_file_exists_no_checkpoint(tmp_path: Path) -> None:
    """Test _check_fragment_data_file_exists when fragment is not checkpointed."""
    db = connect(tmp_path)
    tbl = db.create_table("tbl", pa.table({"a": [1, 2, 3]}))

    store = CheckpointStore.from_uri(str(URL(str(tmp_path)) / "ckp"))
    map_task = BackfillUDFTask(udfs={"one": one})

    # Fragment 0 should not exist in checkpoint store yet
    exists = _check_fragment_data_file_exists(tbl.uri, 0, map_task, store)
    assert not exists


def test_check_fragment_data_file_exists_with_staging_file(tmp_path: Path) -> None:
    """Test _check_fragment_data_file_exists when fragment file exists in staging."""
    db = connect(tmp_path)
    tbl = db.create_table("tbl", pa.table({"a": [1, 2, 3]}))

    store = CheckpointStore.from_uri(str(URL(str(tmp_path)) / "ckp"))
    map_task = BackfillUDFTask(udfs={"one": one})

    # Create a checkpoint entry for fragment 0
    dedupe_key = _get_fragment_dedupe_key(tbl.uri, 0, map_task)
    fake_file_path = "test_fragment_0.lance"
    store[dedupe_key] = pa.RecordBatch.from_pydict({"file": [fake_file_path]})

    # Create the staging file
    staging_dir = tmp_path / "data"
    staging_dir.mkdir(exist_ok=True)
    staging_file = staging_dir / fake_file_path
    staging_file.touch()

    # Should return True since file exists in staging
    exists = _check_fragment_data_file_exists(tbl.uri, 0, map_task, store)
    assert exists


def test_check_fragment_data_file_exists_with_cloud_url() -> None:
    """Test _check_fragment_data_file_exists with cloud URLs."""
    # Create a mock checkpoint store
    store = {}
    map_task = BackfillUDFTask(udfs={"one": one})

    # Test with S3 URL - should not crash but return False since no real file
    s3_uri = "s3://test-bucket/dataset"
    exists = _check_fragment_data_file_exists(s3_uri, 0, map_task, store)
    assert not exists

    # Test with GCS URL - should not crash but return False since no real file
    gcs_uri = "gs://test-bucket/dataset"
    exists = _check_fragment_data_file_exists(gcs_uri, 0, map_task, store)
    assert not exists


def test_plan_read_with_skipped_fragments(tmp_path: Path) -> None:
    """Test that plan_read correctly identifies and skips fragments."""
    db = connect(tmp_path)
    tbl = db.create_table("tbl", pa.table({"a": [1, 2, 3]}))
    tbl.add(pa.table({"a": [4, 5, 6]}))  # Add second fragment

    store = CheckpointStore.from_uri(str(URL(str(tmp_path)) / "ckp"))
    map_task = BackfillUDFTask(udfs={"one": one})

    # Create checkpoint for fragment 0 only
    dedupe_key = _get_fragment_dedupe_key(tbl.uri, 0, map_task)
    fake_file_path = "fragment_0.lance"
    store[dedupe_key] = pa.RecordBatch.from_pydict({"file": [fake_file_path]})

    # Create the staging file for fragment 0
    staging_dir = tmp_path / "data"
    staging_dir.mkdir(exist_ok=True)
    staging_file = staging_dir / fake_file_path
    staging_file.touch()

    # Plan read with checkpoint information
    plans, pipeline_args = plan_read(
        tbl.uri, ["a"], batch_size=16, map_task=map_task, checkpoint_store=store
    )

    # Should still have tasks for fragment 1 (not checkpointed)
    task_list = list(plans)
    assert len(task_list) > 0  # Fragment 1 should have tasks

    # Check that skipped_fragments contains fragment 0
    assert "skipped_fragments" in pipeline_args
    skipped_fragments = pipeline_args["skipped_fragments"]
    assert 0 in skipped_fragments
    assert 1 not in skipped_fragments  # Fragment 1 should not be skipped


def test_plan_read_no_checkpointing_params(tmp_path: Path) -> None:
    """Test that plan_read works normally when no checkpointing params are provided."""
    db = connect(tmp_path)
    tbl = db.create_table("tbl", pa.table({"a": [1, 2, 3]}))

    # Plan read without checkpoint information
    plans, pipeline_args = plan_read(tbl.uri, ["a"], batch_size=16)

    # Should have tasks for all fragments
    task_list = list(plans)
    assert len(task_list) == 1

    # Should have empty skipped_fragments
    assert "skipped_fragments" in pipeline_args
    skipped_fragments = pipeline_args["skipped_fragments"]
    assert len(skipped_fragments) == 0


def test_fragment_writer_manager_with_skipped_fragments(tmp_path: Path) -> None:
    """Test that FragmentWriterManager correctly handles skipped fragments."""
    import lance.fragment
    import ray

    from geneva.runners.ray.actor_pool import JobTracker

    # Start Ray if not already started
    if not ray.is_initialized():
        ray.init(local_mode=True, ignore_reinit_error=True)

    try:
        db = connect(tmp_path)
        tbl = db.create_table("tbl", pa.table({"a": [1, 2, 3]}))

        store = CheckpointStore.from_uri(str(URL(str(tmp_path)) / "ckp"))
        map_task = BackfillUDFTask(udfs={"one": one})

        # Create a mock skipped fragment data file
        skipped_data_file = lance.fragment.DataFile(
            "skipped_fragment.lance",
            [],  # field_ids
            [],  # field_id_to_column_indices
            2,  # major_version
            0,  # minor_version
        )

        skipped_fragments = {0: skipped_data_file}

        # Create job tracker
        job_tracker = JobTracker.remote("test_job")

        # Create FragmentWriterManager with skipped fragments
        fwm = FragmentWriterManager(
            dst_read_version=tbl.version,
            ds_uri=tbl.uri,
            map_task=map_task,
            checkpoint_store=store,
            where=None,
            job_tracker=job_tracker,
            commit_granularity=1,
            expected_tasks={1: 1},  # Only fragment 1 has expected tasks
            skipped_fragments=skipped_fragments,
        )

        # Check that skipped fragment is immediately in to_commit
        assert len(fwm.to_commit) == 1
        frag_id, data_file, row_count = fwm.to_commit[0]
        assert frag_id == 0
        assert data_file == skipped_data_file
        assert row_count >= 0  # Row count should be determined

    finally:
        if ray.is_initialized():
            ray.shutdown()


def test_fragment_writer_manager_no_skipped_fragments(tmp_path: Path) -> None:
    """Test that FragmentWriterManager works normally with no skipped fragments."""
    import ray

    from geneva.runners.ray.actor_pool import JobTracker

    # Start Ray if not already started
    if not ray.is_initialized():
        ray.init(local_mode=True, ignore_reinit_error=True)

    try:
        db = connect(tmp_path)
        tbl = db.create_table("tbl", pa.table({"a": [1, 2, 3]}))

        store = CheckpointStore.from_uri(str(URL(str(tmp_path)) / "ckp"))
        map_task = BackfillUDFTask(udfs={"one": one})

        # Create job tracker
        job_tracker = JobTracker.remote("test_job")

        # Create FragmentWriterManager with no skipped fragments
        fwm = FragmentWriterManager(
            dst_read_version=tbl.version,
            ds_uri=tbl.uri,
            map_task=map_task,
            checkpoint_store=store,
            where=None,
            job_tracker=job_tracker,
            commit_granularity=1,
            expected_tasks={0: 1},  # Fragment 0 has expected tasks
            skipped_fragments={},  # No skipped fragments
        )

        # Should have no items in to_commit initially
        assert len(fwm.to_commit) == 0

    finally:
        if ray.is_initialized():
            ray.shutdown()


def test_fragment_writer_manager_mixed_fragments(tmp_path: Path) -> None:
    """Test FragmentWriterManager with both skipped and normal fragments."""
    import lance.fragment
    import ray

    from geneva.runners.ray.actor_pool import JobTracker

    # Start Ray if not already started
    if not ray.is_initialized():
        ray.init(local_mode=True, ignore_reinit_error=True)

    try:
        db = connect(tmp_path)
        tbl = db.create_table("tbl", pa.table({"a": [1, 2, 3]}))
        tbl.add(pa.table({"a": [4, 5, 6]}))  # Add second fragment

        store = CheckpointStore.from_uri(str(URL(str(tmp_path)) / "ckp"))
        map_task = BackfillUDFTask(udfs={"one": one})

        # Create a mock skipped fragment data file for fragment 0
        skipped_data_file = lance.fragment.DataFile(
            "skipped_fragment_0.lance",
            [],  # field_ids
            [],  # field_id_to_column_indices
            2,  # major_version
            0,  # minor_version
        )

        skipped_fragments = {0: skipped_data_file}

        # Create job tracker
        job_tracker = JobTracker.remote("test_job")

        # Create FragmentWriterManager with mixed fragments
        fwm = FragmentWriterManager(
            dst_read_version=tbl.version,
            ds_uri=tbl.uri,
            map_task=map_task,
            checkpoint_store=store,
            where=None,
            job_tracker=job_tracker,
            commit_granularity=1,
            expected_tasks={1: 1},  # Only fragment 1 has expected tasks to process
            skipped_fragments=skipped_fragments,
        )

        # Should have 1 item in to_commit (the skipped fragment)
        assert len(fwm.to_commit) == 1
        frag_id, data_file, row_count = fwm.to_commit[0]
        assert frag_id == 0
        assert data_file == skipped_data_file

        # Fragment 1 should still be tracked in remaining_tasks
        assert 1 in fwm.remaining_tasks
        assert fwm.remaining_tasks[1] == 1

    finally:
        if ray.is_initialized():
            ray.shutdown()
