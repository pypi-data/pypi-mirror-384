# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright The Geneva Authors

"""
Integration test-specific fixtures.

Common fixtures are inherited from src/conftest.py.
This file only contains fixtures specific to integration tests.
"""

# Import the logger from shared conftest
import logging
import os
import uuid
from collections.abc import Generator

import kubernetes
import pytest
import yaml

from geneva.cluster import K8sConfigMethod
from geneva.runners.kuberay.client import KuberayClients
from geneva.runners.ray.raycluster import RayCluster

_LOG = logging.getLogger(__name__)


# ============================================================================
# Integration test-specific fixtures
# ============================================================================


@pytest.fixture(autouse=False, scope="session")
def kuberay_clients(
    k8s_config_method: K8sConfigMethod, region: str, k8s_cluster_name: str
) -> KuberayClients:
    """KubeRay API clients for integration tests."""
    return KuberayClients(
        config_method=k8s_config_method,
        region=region,
        cluster_name=k8s_cluster_name,
        role_name="geneva-client-role",
    )


@pytest.fixture(autouse=True)
def k8s_temp_service_account(
    kuberay_clients: KuberayClients,
    k8s_namespace: str,
) -> Generator[str, None, None]:
    """Create and cleanup a temporary Kubernetes service account for tests."""
    name = f"geneva-test-{uuid.uuid4().hex}"
    # note: this requires RBAC permissions beyond what we require for Geneva end users
    # namely: ```
    # - apiGroups:
    #   - ""
    #   resources:
    #   - serviceaccounts
    #   verbs:
    #   - create
    #   - delete```
    kuberay_clients.core_api.create_namespaced_service_account(
        namespace=k8s_namespace,
        body={
            "apiVersion": "v1",
            "kind": "ServiceAccount",
            "metadata": {
                "name": name,
                "namespace": k8s_namespace,
            },
        },
    )
    yield name
    kuberay_clients.core_api.delete_namespaced_service_account(
        name=name,
        namespace=k8s_namespace,
        body=kubernetes.client.V1DeleteOptions(),
    )


@pytest.fixture(autouse=False)
def k8s_temp_config_map(
    kuberay_clients: KuberayClients,
    k8s_namespace: str,
    csp: str,
) -> Generator[str, None, None]:
    """Create and cleanup a temporary Kubernetes ConfigMap for cluster configuration."""
    src = os.path.join(
        os.path.dirname(__file__),
        "../tests/test_configs/raycluster-configmap.yaml",
    )
    name = f"geneva-test-cluster-config-{uuid.uuid4().hex}"
    with open(src) as f:
        cm_spec = yaml.safe_load(f)
        # override metadata name/namespace
        cm_spec.setdefault("metadata", {})
        cm_spec["metadata"]["name"] = name
        cm_spec["metadata"]["namespace"] = k8s_namespace

        if csp == "gcp":
            # todo: remove this hack after https://linear.app/lancedb/issue/GEN-60/make-node-selectors-consistent-between-eksgks
            hg = cm_spec["data"]["head_group"]
            hg = hg.replace(
                'geneva.lancedb.com/ray-head: "true"',
                'geneva.lancedb.com/ray-head: ""',
            )
            cm_spec["data"]["head_group"] = hg
            wgs = cm_spec["data"]["worker_groups"]
            wgs = wgs.replace(
                'geneva.lancedb.com/ray-worker-gpu: "true"',
                'geneva.lancedb.com/ray-worker-gpu: ""',
            ).replace(
                'geneva.lancedb.com/ray-worker-cpu: "true"',
                'geneva.lancedb.com/ray-worker-cpu: ""',
            )
            cm_spec["data"]["worker_groups"] = wgs

        body = kubernetes.client.V1ConfigMap(
            api_version=cm_spec.get("apiVersion"),
            kind=cm_spec.get("kind"),
            metadata=kubernetes.client.V1ObjectMeta(**cm_spec["metadata"]),
            data=cm_spec.get("data", {}),
        )
        kuberay_clients.core_api.create_namespaced_config_map(
            namespace=k8s_namespace,
            body=body,
        )
        yield name
    kuberay_clients.core_api.delete_namespaced_config_map(
        name=name,
        namespace=k8s_namespace,
    )


@pytest.fixture(autouse=False)
def cluster_from_config_map(
    k8s_temp_config_map: str,
    k8s_config_method: K8sConfigMethod,
    k8s_namespace: str,
    region: str,
    k8s_cluster_name: str,
    slug: str | None,
) -> RayCluster:
    """Create a Ray cluster from a Kubernetes ConfigMap."""
    from geneva.runners.ray.raycluster import RayCluster
    from geneva.utils import dt_now_utc

    ray_cluster_name = "configmap-cluster"
    ray_cluster_name += f"-{dt_now_utc().strftime('%Y-%m-%d-%H-%M')}-{slug}"

    return RayCluster.from_config_map(
        k8s_namespace,
        k8s_cluster_name,
        k8s_temp_config_map,
        ray_cluster_name,
        # only needed for EKS auth
        config_method=k8s_config_method,
        aws_region=region,
    )
