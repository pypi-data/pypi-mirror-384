# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright The Geneva Authors
from collections.abc import Generator
from typing import Any

import pytest
import ray
import yaml

try:
    from geneva.runners.ray.raycluster import (
        RayCluster,
        _HeadGroupSpec,
        _WorkerGroupSpec,
    )
except ImportError:
    pytest.skip("failed to import geneva.runners.ray", allow_module_level=True)

# Disable real k8s client init in attrs post_init for serialization tests
RayCluster.__attrs_post_init__ = lambda self: None


@pytest.fixture(autouse=True)
def ensure_ray_shutdown() -> Generator[None, None, None]:
    """Ensure Ray is shut down before and after each test"""
    if ray.is_initialized():
        ray.shutdown()
    yield
    if ray.is_initialized():
        ray.shutdown()


class DummyCM:
    def __init__(self, data: dict[str, str]) -> None:
        self.data = data


def test_env_vars_in_head_and_worker() -> None:
    """Test that env_vars can be set on both head and worker groups and
    appear in pod definition"""
    head = _HeadGroupSpec(
        env_vars={
            "GCS_REQUEST_CONNECTION_TIMEOUT_SECS": "300",
            "GCS_REQUEST_TIMEOUT_SECS": "600",
            "CUSTOM_VAR": "value",
        }
    )
    worker = _WorkerGroupSpec(
        env_vars={
            "GCS_REQUEST_CONNECTION_TIMEOUT_SECS": "300",
            "GCS_REQUEST_TIMEOUT_SECS": "600",
            "WORKER_VAR": "worker_value",
        }
    )

    cluster = RayCluster(
        name="test-env-vars", namespace="test", head_group=head, worker_groups=[worker]
    )

    # Check head group container env vars in the generated definition
    head_spec = cluster.definition["spec"]["headGroupSpec"]
    head_container = head_spec["template"]["spec"]["containers"][0]
    assert "env" in head_container
    head_env = {env["name"]: env["value"] for env in head_container["env"]}
    assert head_env["GCS_REQUEST_CONNECTION_TIMEOUT_SECS"] == "300"
    assert head_env["GCS_REQUEST_TIMEOUT_SECS"] == "600"
    assert head_env["CUSTOM_VAR"] == "value"
    assert len(head_env) == 3

    # Check worker group container env vars in the generated definition
    worker_spec = cluster.definition["spec"]["workerGroupSpecs"][0]
    worker_container = worker_spec["template"]["spec"]["containers"][0]
    assert "env" in worker_container
    worker_env = {env["name"]: env["value"] for env in worker_container["env"]}
    # Worker has 2 default env vars (RAY_memory_usage_threshold,
    # RAY_memory_monitor_refresh_ms) plus the 3 custom ones
    assert worker_env["GCS_REQUEST_CONNECTION_TIMEOUT_SECS"] == "300"
    assert worker_env["GCS_REQUEST_TIMEOUT_SECS"] == "600"
    assert worker_env["WORKER_VAR"] == "worker_value"
    assert worker_env["RAY_memory_usage_threshold"] == "0.9"
    assert worker_env["RAY_memory_monitor_refresh_ms"] == "0"
    assert len(worker_env) == 5


def test_env_vars_empty() -> None:
    """Test that empty env_vars dict produces empty env list"""
    head = _HeadGroupSpec(env_vars={})
    worker = _WorkerGroupSpec(env_vars={})

    cluster = RayCluster(
        name="test-empty-env", namespace="test", head_group=head, worker_groups=[worker]
    )

    # Check head group has empty env list
    head_spec = cluster.definition["spec"]["headGroupSpec"]
    head_container = head_spec["template"]["spec"]["containers"][0]
    assert head_container["env"] == []

    # Check worker group has only default env vars
    worker_spec = cluster.definition["spec"]["workerGroupSpecs"][0]
    worker_container = worker_spec["template"]["spec"]["containers"][0]
    worker_env = {env["name"]: env["value"] for env in worker_container["env"]}
    assert worker_env["RAY_memory_usage_threshold"] == "0.9"
    assert worker_env["RAY_memory_monitor_refresh_ms"] == "0"
    assert len(worker_env) == 2


def test_env_vars_serialization_to_config_map() -> None:
    """Test that env_vars are preserved in ConfigMap serialization"""
    head = _HeadGroupSpec(
        image="img",
        num_cpus=1,
        memory="4Gi",
        env_vars={"HEAD_VAR": "head_value"},
    )
    worker = _WorkerGroupSpec(
        image="img",
        num_cpus=2,
        memory="8Gi",
        env_vars={"WORKER_VAR": "worker_value"},
    )

    cluster = RayCluster(
        name="test-env-serialization",
        namespace="ns",
        head_group=head,
        worker_groups=[worker],
    )

    data = cluster.to_config_map()
    h = yaml.safe_load(data["head_group"])
    assert h["env_vars"] == {"HEAD_VAR": "head_value"}

    ws = yaml.safe_load(data["worker_groups"])
    assert ws[0]["env_vars"] == {"WORKER_VAR": "worker_value"}


def test_env_vars_deserialization_from_config_map(monkeypatch) -> None:
    """Test that env_vars are properly loaded from ConfigMap"""
    dummy_data = {
        "name": "env-vars-cluster",
        "head_group": yaml.dump(
            {
                "image": "ray:latest",
                "num_cpus": 2,
                "memory": "4Gi",
                "env_vars": {"HEAD_ENV": "head_val"},
            }
        ),
        "worker_groups": yaml.dump(
            [
                {
                    "image": "ray:latest",
                    "num_cpus": 4,
                    "memory": "8Gi",
                    "env_vars": {"WORKER_ENV": "worker_val"},
                }
            ]
        ),
    }
    cm = DummyCM(dummy_data)

    monkeypatch.setattr(
        "geneva.runners.kuberay.client.build_api_client",
        lambda *args: None,
    )

    class DummyCore:
        def read_namespaced_config_map(self, name: str, namespace: str) -> DummyCM:
            return cm

    monkeypatch.setattr(
        "geneva.runners.ray.raycluster.kubernetes.client.CoreV1Api",
        lambda api_client=None: DummyCore(),
    )

    cluster = RayCluster.from_config_map(
        "my-namespace", "my-k8s-cluster", "cm-name", "env-vars-cluster"
    )

    assert cluster.head_group.env_vars == {"HEAD_ENV": "head_val"}
    assert cluster.worker_groups[0].env_vars == {"WORKER_ENV": "worker_val"}


def test_extra_env_passed_to_init_ray(monkeypatch) -> None:
    """Test that extra_env parameter is passed through ray_cluster to init_ray

    This test verifies that extra_env variables are correctly passed through the
    ray_cluster context manager to init_ray, where they become part of Ray's
    runtime environment. These variables will be available in Ray worker processes
    when executing tasks/actors on both head and worker nodes.
    """

    import geneva.runners.ray._mgr as ray_mgr_mod

    ray_init_called = {}

    # Mock ray.init to capture the runtime_env
    def mock_ray_init(*args: Any, **kwargs: Any) -> None:
        ray_init_called["args"] = args
        ray_init_called["kwargs"] = kwargs

    monkeypatch.setattr("ray.init", mock_ray_init)
    monkeypatch.setattr("ray.shutdown", lambda: None)
    monkeypatch.setattr("ray.is_initialized", lambda: False)

    # Test with local ray cluster to avoid kubernetes dependencies
    extra_env_vars = {
        "GCS_REQUEST_CONNECTION_TIMEOUT_SECS": "300",
        "GCS_REQUEST_TIMEOUT_SECS": "600",
        "CUSTOM_ENV_VAR": "custom_value",
    }

    with ray_mgr_mod.ray_cluster(local=True, extra_env=extra_env_vars):
        pass

    # Verify ray.init was called with correct runtime_env
    assert "kwargs" in ray_init_called
    runtime_env = ray_init_called["kwargs"]["runtime_env"]

    # Check that extra_env variables are in the runtime_env
    assert "env_vars" in runtime_env
    env_vars = runtime_env["env_vars"]

    # Verify our custom env vars are present
    assert env_vars["GCS_REQUEST_CONNECTION_TIMEOUT_SECS"] == "300"
    assert env_vars["GCS_REQUEST_TIMEOUT_SECS"] == "600"
    assert env_vars["CUSTOM_ENV_VAR"] == "custom_value"

    # GENEVA_ZIPS should also be present (added by init_ray)
    assert "GENEVA_ZIPS" in env_vars


def test_env_vars_vs_extra_env(monkeypatch) -> None:
    """Test interaction between env_vars (in head spec) and extra_env

    This test demonstrates that:
    - env_vars in head/worker specs set Kubernetes container environment variables
    - extra_env in ray_cluster sets Ray runtime_env environment variables
    - When the same variable is set in both places, extra_env takes
      precedence in Ray tasks
    - extra_env is what gets passed to init_ray's runtime_env, not env_vars
      from specs
    """

    import geneva.runners.ray._mgr as ray_mgr_mod

    ray_init_called = {}

    # Mock ray.init to capture the runtime_env
    def mock_ray_init(*args: Any, **kwargs: Any) -> None:
        ray_init_called["args"] = args
        ray_init_called["kwargs"] = kwargs

    monkeypatch.setattr("ray.init", mock_ray_init)
    monkeypatch.setattr("ray.shutdown", lambda: None)
    monkeypatch.setattr("ray.is_initialized", lambda: False)

    # Create a RayCluster with env_vars in the head spec
    # These would normally go into the Kubernetes pod definition
    head = _HeadGroupSpec(
        env_vars={
            "SHARED_VAR": "from_head_spec",
            "HEAD_ONLY_VAR": "head_value",
        }
    )
    # Note: cluster object is not used, but demonstrates that env_vars
    # in head spec don't automatically flow to runtime_env
    _ = RayCluster(
        name="test-env-conflict",
        namespace="test",
        head_group=head,
        worker_groups=[],
    )

    # Now use ray_cluster with extra_env
    # These go into Ray's runtime_env
    extra_env_vars = {
        "SHARED_VAR": "from_extra_env",  # Overlaps with head spec
        "EXTRA_ONLY_VAR": "extra_value",  # Only in extra_env
    }

    # Note: We use local=True to avoid actually creating a k8s cluster
    # In a real scenario with a k8s cluster, both env_vars (in containers)
    # and extra_env (in Ray runtime_env) would be present
    with ray_mgr_mod.ray_cluster(local=True, extra_env=extra_env_vars):
        pass

    # Verify what ended up in the runtime_env
    assert "kwargs" in ray_init_called
    runtime_env = ray_init_called["kwargs"]["runtime_env"]
    assert "env_vars" in runtime_env
    env_vars = runtime_env["env_vars"]

    # Key insight: Only extra_env makes it to the runtime_env
    # The env_vars from head spec are NOT in the runtime_env
    # (they would only be in the Kubernetes pod definition)
    assert env_vars["SHARED_VAR"] == "from_extra_env"  # extra_env wins for Ray tasks
    assert env_vars["EXTRA_ONLY_VAR"] == "extra_value"
    assert "HEAD_ONLY_VAR" not in env_vars  # Not in runtime_env
    assert "GENEVA_ZIPS" in env_vars  # Always present


def test_extra_env_available_in_ray_workers() -> None:
    """Test that extra_env variables are actually available in Ray worker processes

    This integration test starts a real local Ray cluster and verifies that
    environment variables passed via extra_env are accessible in Ray remote
    functions running on worker processes.
    """
    import os

    import ray

    import geneva.runners.ray._mgr as ray_mgr_mod

    # Define a remote function that checks environment variables
    @ray.remote
    def check_env_vars() -> dict[str, str | None]:
        """Remote function that runs in a Ray worker and checks env vars"""
        return {
            "GCS_REQUEST_CONNECTION_TIMEOUT_SECS": os.environ.get(
                "GCS_REQUEST_CONNECTION_TIMEOUT_SECS"
            ),
            "GCS_REQUEST_TIMEOUT_SECS": os.environ.get("GCS_REQUEST_TIMEOUT_SECS"),
            "CUSTOM_ENV_VAR": os.environ.get("CUSTOM_ENV_VAR"),
        }

    extra_env_vars = {
        "GCS_REQUEST_CONNECTION_TIMEOUT_SECS": "300",
        "GCS_REQUEST_TIMEOUT_SECS": "600",
        "CUSTOM_ENV_VAR": "custom_value",
    }

    # Use local Ray cluster to test
    with ray_mgr_mod.ray_cluster(local=True, extra_env=extra_env_vars):
        # Execute the remote function and get the result
        result = ray.get(check_env_vars.remote())

        # Verify all env vars are accessible in the worker
        assert result["GCS_REQUEST_CONNECTION_TIMEOUT_SECS"] == "300"
        assert result["GCS_REQUEST_TIMEOUT_SECS"] == "600"
        assert result["CUSTOM_ENV_VAR"] == "custom_value"
