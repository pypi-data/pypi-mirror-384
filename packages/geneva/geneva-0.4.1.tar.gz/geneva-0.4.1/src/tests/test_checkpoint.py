# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright The Geneva Authors

import tempfile

import pyarrow as pa
import pytest

from geneva.checkpoint import (
    CheckpointConfig,
    CheckpointStore,
    InMemoryCheckpointStore,
    LanceCheckpointStore,
    LanceSessionizedCheckpointStore,
)


@pytest.mark.parametrize(
    "store",
    [
        InMemoryCheckpointStore(),
        LanceCheckpointStore(f"{tempfile.mkdtemp()}/new_dir"),
        LanceSessionizedCheckpointStore(f"{tempfile.mkdtemp()}/new_dir2"),
    ],
)
def test_checkpoint(store: CheckpointStore) -> None:
    store["key"] = pa.RecordBatch.from_pydict({"a": [1, 2, 3]})
    assert "key" in store
    assert "key" in list(store.list_keys())
    assert store["key"].to_pydict() == {"a": [1, 2, 3]}


def test_default_ckp_store() -> None:
    store = CheckpointConfig(mode="tempfile").make()
    assert isinstance(store, LanceCheckpointStore)
    assert store.root.startswith(tempfile.gettempdir())
