# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright The Geneva Authors

"""
E2E test-specific fixtures.

Common fixtures are inherited from src/conftest.py.
This file only contains fixtures specific to e2e tests.
"""

import contextlib
import logging
from collections.abc import Generator

import pyarrow as pa
import pytest

from geneva.cluster import K8sConfigMethod
from geneva.runners.ray._mgr import ray_cluster
from geneva.runners.ray.raycluster import ExitMode, _HeadGroupSpec, _WorkerGroupSpec
from geneva.utils import dt_now_utc

_LOG = logging.getLogger(__name__)


# ============================================================================
# E2E test-specific pytest options
# ============================================================================


def pytest_addoption(parser) -> None:
    """Add e2e-specific command-line options."""
    # Add e2e-specific options
    parser.addoption(
        "--num-images",
        action="store",
        type=int,
        default=500,
        help="Number of images to process from Oxford pets dataset",
    )
    parser.addoption(
        "--batch-size",
        action="store",
        type=int,
        default=10,
        help="Batch size for backfill operations",
    )
    parser.addoption(
        "--skip-gpu",
        action="store_true",
        default=False,
        help="Skip GPU-based tests (captions, GPU embeddings)",
    )


# ============================================================================
# Dataset Loading Utilities
# ============================================================================

ImageBatchGenerator = Generator[pa.RecordBatch, None, None]


def load_oxford_pets_images(
    num_images: int = 500, frag_size: int = 25
) -> ImageBatchGenerator:
    """
    Load images from the Oxford-IIIT Pet dataset.

    Args:
        num_images: Number of images to load from the dataset
        frag_size: Number of images per fragment

    Yields:
        PyArrow RecordBatch with columns: image (bytes), label (string)

    Raises:
        pytest.skip: If dataset cannot be loaded due to network or API errors
    """
    import io

    import pyarrow as pa
    from datasets import load_dataset

    from geneva.tqdm import tqdm

    _LOG.info(f"Loading {num_images} images from Oxford pets dataset")

    try:
        # there are 3680 images.  If num_images > 3680, it will just load all
        dataset = load_dataset("timm/oxford-iiit-pet", split=f"train[:{num_images}]")
    except Exception as e:
        pytest.skip(
            f"Failed to load Oxford pets dataset from HuggingFace. "
            f"This may be due to network issues or API unavailability. Error: {e}"
        )

    batch = []
    for row in tqdm(dataset):
        buf = io.BytesIO()
        row["image"].save(buf, format="png")
        batch.append({"image": buf.getvalue(), "label": row["label"]})

        if len(batch) >= frag_size:
            yield pa.RecordBatch.from_pylist(batch)
            batch = []

    if batch:
        yield pa.RecordBatch.from_pylist(batch)


# ============================================================================
# E2E test-specific fixtures
# ============================================================================


@pytest.fixture(scope="session")
def num_images(request) -> int:
    """Number of images to process in e2e tests."""
    return request.config.getoption("--num-images")


@pytest.fixture(scope="session")
def batch_size(request) -> int:
    """Batch size for backfill operations in e2e tests."""
    return request.config.getoption("--batch-size")


@pytest.fixture(scope="session")
def skip_gpu(request) -> bool:
    """Whether to skip GPU-based tests."""
    return request.config.getoption("--skip-gpu")


@pytest.fixture(scope="session")
def oxford_pets_table(geneva_test_bucket: str, num_images: int) -> tuple:  # type: ignore[misc]
    """
    Session-scoped fixture that creates a shared table with Oxford pets images.

    This table is created once per test session and reused across all e2e tests,
    avoiding repeated dataset downloads.

    Returns:
        tuple: (connection, table, table_name)
    """
    import uuid

    import geneva

    _LOG.info(f"Creating shared Oxford pets table with {num_images} images")

    conn = geneva.connect(geneva_test_bucket)
    table_name = f"oxford_pets_shared_{uuid.uuid4().hex}"

    # Load images and create table (only happens once per session)
    first = True
    for batch in load_oxford_pets_images(num_images):
        if first:
            tbl = conn.create_table(table_name, batch, mode="overwrite")
            first = False
        else:
            tbl.add(batch)

    _LOG.info(
        f"Shared table '{table_name}' created with {len(tbl)} rows. "
        "This will be reused across all e2e tests."
    )

    yield conn, tbl, table_name

    # Cleanup after all tests complete
    _LOG.info(f"Cleaning up shared table '{table_name}'")
    try:
        conn.drop_table(table_name)
    except Exception as e:
        _LOG.warning(f"Failed to cleanup table {table_name}: {e}")


@pytest.fixture
def gpu_cluster(
    geneva_k8s_service_account: str,
    k8s_config_method: K8sConfigMethod,
    k8s_namespace: str,
    csp: str,
    region: str,
    head_node_selector: dict,
    k8s_cluster_name: str,
    slug: str | None,
) -> contextlib.AbstractContextManager:
    """Ray cluster with GPU workers for caption and embedding generation."""
    ray_cluster_name = "e2e-gpu-cluster"
    ray_cluster_name += f"-{dt_now_utc().strftime('%Y-%m-%d-%H-%M')}-{slug}"

    _LOG.info(f"creating GPU ray cluster {ray_cluster_name}")

    head_spec = _HeadGroupSpec(  # type: ignore[call-arg]
        service_account=geneva_k8s_service_account,
        num_cpus=1,
        memory=3 * 1024**3,
        node_selector=head_node_selector,
    )

    # GPU worker
    gpu_worker_node_selector = (
        {"geneva.lancedb.com/ray-worker-gpu": "true"}
        if csp == "aws"
        else {"_PLACEHOLDER": "true"}
    )

    worker_spec = _WorkerGroupSpec(  # type: ignore[call-arg]
        name="gpu-worker",
        min_replicas=0,
        service_account=geneva_k8s_service_account,
        num_cpus=4,
        memory=16 * 1024**3,
        node_selector=gpu_worker_node_selector,
        num_gpus=1,
    )

    return ray_cluster(
        name=ray_cluster_name,
        namespace=k8s_namespace,
        config_method=k8s_config_method,
        region=region,
        use_portforwarding=True,
        head_group=head_spec,
        worker_groups=[worker_spec],
        cluster_name=k8s_cluster_name,
        role_name="geneva-client-role",
        on_exit=ExitMode.DELETE,
        extra_env={
            "RAY_BACKEND_LOG_LEVEL": "debug",
            "RAY_LOG_TO_DRIVER": "1",
            "RAY_ENABLE_RECORD_ACTOR_TASK_LOGGING": "1",
            "RAY_RUNTIME_ENV_LOG_TO_DRIVER_ENABLED": "true",
        },
        log_to_driver=True,
        logging_level=logging.DEBUG,
    )
