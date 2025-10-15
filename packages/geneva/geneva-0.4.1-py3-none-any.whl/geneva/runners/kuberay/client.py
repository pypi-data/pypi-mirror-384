# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright The Geneva Authors

import functools
import logging
from collections.abc import Callable
from typing import Any

import attrs
import kubernetes
from kubernetes import client
from kubernetes.client import ApiException

from geneva.cluster import K8sConfigMethod
from geneva.eks import build_api_client

_LOG = logging.getLogger(__name__)


def _refresh_auth(clients: "KuberayClients") -> Callable:
    """Create a refresh_auth decorator for KuberayClients methods"""

    def decorator(func) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            retry_count = 0
            last_exception = None
            while retry_count < 3:
                try:
                    return func(*args, **kwargs)
                except ApiException as e:  # noqa: PERF203
                    _LOG.debug(e)
                    last_exception = e
                    retry_count += 1
                    if e.status != 401:
                        raise e
                    _LOG.info(
                        f"token expired, reauthenticating with k8s, "
                        f"retries={retry_count}"
                    )
                    clients.refresh()

            _LOG.error(f"k8s auth retries exceeded. retries={retry_count}")
            if last_exception is not None:
                raise last_exception
            else:
                raise RuntimeError(
                    "k8s auth retries exceeded with no exception recorded"
                )

        return wrapper

    return decorator


def _wrap_api_methods(api_instance: Any, kuberay_clients_instance: Any) -> Any:
    """Wrap all methods of an API instance with refresh_auth decorator"""
    decorator = _refresh_auth(kuberay_clients_instance)

    for attr_name in dir(api_instance):
        if (
            not attr_name.startswith("_")
            and attr_name != "connect_get_namespaced_pod_portforward"
        ):
            attr = getattr(api_instance, attr_name)
            if callable(attr):
                wrapped_attr = decorator(attr)
                setattr(api_instance, attr_name, wrapped_attr)
    return api_instance


@attrs.define()
class KuberayClients:
    """
    Wrap kubernetes clients required for Kuberay operations
    """

    core_api: client.CoreV1Api = attrs.field(init=False)
    custom_api: client.CustomObjectsApi = attrs.field(init=False)
    auth_api: client.AuthorizationV1Api = attrs.field(init=False)
    scheduling_api: client.SchedulingV1Api = attrs.field(init=False)

    config_method: K8sConfigMethod = attrs.field(default=K8sConfigMethod.LOCAL)
    """
    Method to retrieve kubeconfig
    """

    region: str | None = attrs.field(
        default=None,
    )
    """
    Optional cloud region where the cluster is located
    """

    cluster_name: str | None = attrs.field(
        default=None,
    )
    """
    Optional k8s cluster name, required for EKS auth
    """

    role_name: str | None = attrs.field(
        default=None,
    )
    """
    Optional IAM role name, required for EKS auth
    """

    def __attrs_post_init__(self) -> None:
        self.init_clients()

    def refresh(self) -> None:
        self.init_clients()

    def init_clients(self) -> None:
        self._validate()

        # Initialize API clients based on config_method
        # If refresh is set, it will re-authenticate instead of using cached client
        client = build_api_client(
            self.config_method, self.region, self.cluster_name, self.role_name
        )

        # Create API clients
        self.custom_api = kubernetes.client.CustomObjectsApi(api_client=client)
        self.core_api = kubernetes.client.CoreV1Api(api_client=client)
        self.auth_api = kubernetes.client.AuthorizationV1Api(api_client=client)
        self.scheduling_api = kubernetes.client.SchedulingV1Api(api_client=client)

        # Wrap all API methods with refresh_auth decorator
        _wrap_api_methods(self.custom_api, self)
        _wrap_api_methods(self.core_api, self)
        _wrap_api_methods(self.auth_api, self)
        _wrap_api_methods(self.scheduling_api, self)

    def _validate(self) -> None:
        if self.config_method == K8sConfigMethod.EKS_AUTH:
            # log these and fallback to defaults
            if not self.cluster_name:
                _LOG.warning(
                    "Using default cluster name for config method "
                    "EKS_AUTH because cluster_name is not set"
                )
            if not self.region:
                _LOG.warning(
                    "Using default region for config method "
                    "EKS_AUTH because region is not set"
                )
            if not self.role_name:
                _LOG.warning(
                    "Using default role name for config method "
                    "EKS_AUTH because role_name is not set"
                )
