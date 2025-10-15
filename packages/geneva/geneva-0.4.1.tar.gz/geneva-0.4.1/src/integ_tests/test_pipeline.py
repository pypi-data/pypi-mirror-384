# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright The Geneva Authors

import logging
import time
import uuid

import pyarrow as pa
import pytest
import ray

import geneva
from geneva.runners.ray.raycluster import ClusterStatus, RayCluster

_LOG = logging.getLogger(__name__)


# use a random version to force checkpoint to invalidate
@geneva.udf(num_cpus=1, version=uuid.uuid4().hex)
def plus_one(a: int) -> int:
    return a + 1


SIZE = 1024


def test_get_imported(
    geneva_test_bucket: str,
    standard_cluster: RayCluster,
) -> None:
    from geneva.runners.ray.pipeline import get_imported

    geneva.connect(geneva_test_bucket)
    with standard_cluster:
        pkgs = ray.get(get_imported.remote())
        for pkg, ver in sorted(pkgs.items()):
            _LOG.info(f"{pkg}=={ver}")


def test_ray_add_column_pipeline(
    geneva_test_bucket: str,
    standard_cluster: RayCluster,
) -> None:
    conn = geneva.connect(geneva_test_bucket)
    table_name = uuid.uuid4().hex
    table = conn.create_table(
        table_name,
        pa.Table.from_pydict({"a": pa.array(range(SIZE))}),
    )
    with standard_cluster:
        table.add_columns(
            {"b": plus_one},  # type: ignore[arg-type]
            batch_size=32,
            concurrency=2,
            intra_applier_concurrency=2,
        )
        table.backfill("b")

    assert table.to_arrow() == pa.Table.from_pydict(
        {"a": pa.array(range(SIZE)), "b": pa.array(range(1, SIZE + 1))}
    )
    conn.drop_table(table_name)


@pytest.mark.timeout(300)
def test_ray_add_column_pipeline_backfill_async(
    geneva_test_bucket: str,
    standard_cluster: RayCluster,
) -> None:
    conn = geneva.connect(geneva_test_bucket)
    table_name = uuid.uuid4().hex
    table = conn.create_table(
        table_name,
        pa.Table.from_pydict({"a": pa.array(range(SIZE))}),
    )
    with standard_cluster:
        table.add_columns(
            {"b": plus_one},  # type: ignore[arg-type]
            batch_size=32,
            concurrency=2,
            intra_applier_concurrency=2,
        )
        fut = table.backfill_async("b")
        while not fut.done():
            time.sleep(1)
        table.checkout_latest()

        _LOG.info("FUT pbars: %s", fut._pbars)  # type: ignore[attr-defined]
        # there should be 4 pbars - geneva, checkpointed, ready to commit and committed
        assert len(fut._pbars) == 4  # type: ignore[attr-defined]

        cs = ClusterStatus()
        cs.get_status()
        assert cs.pbar_k8s is not None
        assert cs.pbar_kuberay is not None

    assert table.to_arrow() == pa.Table.from_pydict(
        {"a": pa.array(range(SIZE)), "b": pa.array(range(1, SIZE + 1))}
    )
    conn.drop_table(table_name)


def test_ray_add_column_pipeline_cpu_only_pool(
    geneva_test_bucket: str,
    standard_cluster: RayCluster,
) -> None:
    conn = geneva.connect(geneva_test_bucket)
    table_name = uuid.uuid4().hex
    table = conn.create_table(
        table_name,
        pa.Table.from_pydict({"a": pa.array(range(SIZE))}),
    )
    with standard_cluster:
        table.add_columns(
            {"b": plus_one},  # type: ignore[arg-type]
            batch_size=32,
            concurrency=4,
            use_cpu_only_pool=True,
        )
        table.backfill("b")

    assert table.to_arrow() == pa.Table.from_pydict(
        {"a": pa.array(range(SIZE)), "b": pa.array(range(1, SIZE + 1))}
    )
    conn.drop_table(table_name)
