import ast

import ray
from kubernetes import config as kube_config
from ray.util.state.common import ActorState

from geneva.cluster import K8sConfigMethod
from geneva.runners.kuberay.client import KuberayClients
from geneva.runners.ray.kuberay import _ray_status, k8s_status

# ray.nodes() output
ray_nodes_json = """
[{'NodeID': 'b80f1624b03cd1af6714e2dc1d6f9f9eea14799ad52bde6057f44bf1',
  'Alive': True,
  'NodeManagerAddress': '172.17.78.133',
  'NodeManagerHostname': 'scorponok',
  'NodeManagerPort': 33027,
  'ObjectManagerPort': 45027,
  'ObjectStoreSocketName': '/tmp/ray/session_2025-06-17_15-05-30_021933_564383/sockets/plasma_store',
  'RayletSocketName': '/tmp/ray/session_2025-06-17_15-05-30_021933_564383/sockets/raylet',
  'MetricsExportPort': 64855,
  'NodeName': '172.17.78.133',
  'RuntimeEnvAgentPort': 53410,
  'DeathReason': 0,
  'DeathReasonMessage': '',
  'alive': True,
  'Resources': {'memory': 31255464756.0,
   'node:__internal_head__': 1.0,
   'GPU': 1.0,
   'object_store_memory': 13395199180.0,
   'node:172.17.78.133': 1.0,
   'CPU': 32.0,
   'accelerator_type:RTX': 1.0},
  'Labels': {'ray.io/node_id': 'b80f1624b03cd1af6714e2dc1d6f9f9eea14799ad52bde6057f44bf1'}}]
"""  # noqa: E501

# Sample dump from ray.util.state.list_actors
"""
[ActorState(actor_id='4d1e4fe662ba5e26aa06f46c01000000', class_name='ApplierActor',
    state='DEAD', job_id='01000000', name='file_size::images',
    node_id='e227e86b72a0e9340c3eaec24cbdc2606830fc63b770583640205c95', pid=657551,
    ray_namespace='4490874b-64d4-4140-8195-c32247ccb2af', serialized_runtime_env=None,
    required_resources=None, death_cause=None, is_detached=None, placement_group_id=None,
    repr_name=None, num_restarts=None, num_restarts_due_to_lineage_reconstruction=None,
    call_site=None),
ActorState(actor_id='4e07c27f63f95807cafe1ea701000000', class_name='ProgressTracker',
    state='ALIVE', job_id='01000000', name='',
    node_id='e227e86b72a0e9340c3eaec24cbdc2606830fc63b770583640205c95',
    pid=657553, ray_namespace='4490874b-64d4-4140-8195-c32247ccb2af',
    serialized_runtime_env=None, required_resources=None, death_cause=None,
    is_detached=None, placement_group_id=None, repr_name=None, num_restarts=None,
    num_restarts_due_to_lineage_reconstruction=None, call_site=None),
ActorState(actor_id='5e07c27f63f95807cafe1ea701000000', class_name='ProgressTracker',
    state='PENDING_CREATION', job_id='01000000', name='',
    node_id='e227e86b72a0e9340c3eaec24cbdc2606830fc63b770583640205c95',
    pid=657553, ray_namespace='4490874b-64d4-4140-8195-c32247ccb2af',
    serialized_runtime_env=None, required_resources=None, death_cause=None,
    is_detached=None, placement_group_id=None, repr_name=None, num_restarts=None,
    num_restarts_due_to_lineage_reconstruction=None, call_site=None),
ActorState(actor_id='6e07c27f63f95807cafe1ea701000000', class_name='ProgressTracker',
    state='DEPENDENCIES_UNREADY', job_id='01000000', name='',
    node_id='e227e86b72a0e9340c3eaec24cbdc2606830fc63b770583640205c95',
    pid=657553, ray_namespace='4490874b-64d4-4140-8195-c32247ccb2af',
    serialized_runtime_env=None, required_resources=None, death_cause=None,
    is_detached=None, placement_group_id=None, repr_name=None, num_restarts=None,
    num_restarts_due_to_lineage_reconstruction=None, call_site=None),
ActorState(actor_id='7e07c27f63f95807cafe1ea701000000', class_name='ProgressTracker',
    state='RESTARTING', job_id='01000000', name='',
    node_id='e227e86b72a0e9340c3eaec24cbdc2606830fc63b770583640205c95',
    pid=657553, ray_namespace='4490874b-64d4-4140-8195-c32247ccb2af',
    serialized_runtime_env=None, required_resources=None, death_cause=None,
    is_detached=None, placement_group_id=None, repr_name=None, num_restarts=None,
    num_restarts_due_to_lineage_reconstruction=None, call_site=None),
ActorState(actor_id='8017a2c6bd91443240895bcd01000000', class_name='ProgressTracker',
    state='ALIVE', job_id='01000000', name='',
    node_id='e227e86b72a0e9340c3eaec24cbdc2606830fc63b770583640205c95', pid=657555,
    ray_namespace='4490874b-64d4-4140-8195-c32247ccb2af', serialized_runtime_env=None,
    required_resources=None, death_cause=None, is_detached=None, placement_group_id=None,
    repr_name=None, num_restarts=None, num_restarts_due_to_lineage_reconstruction=None,
    call_site=None)]
"""  # noqa: E501


def make_actor_states() -> list[any]:
    return [
        ActorState(
            actor_id="4d1e4fe662ba5e26aa06f46c01000000",
            class_name="ApplierActor",
            state="DEAD",
            job_id="01000000",
            name="file_size::images",
            node_id="e227e86b72a0e9340c3eaec24cbdc2606830fc63b770583640205c95",
            pid=657551,
            ray_namespace="4490874b-64d4-4140-8195-c32247ccb2af",
        ),
        ActorState(
            actor_id="4d1e4fe662ba5e26aa06f46c01000000",
            class_name="ApplierActor",
            state="ALIVE",
            job_id="01000000",
            name="file_size::images",
            node_id="e227e86b72a0e9340c3eaec24cbdc2606830fc63b770583640205c95",
            pid=657552,
            ray_namespace="4490874b-64d4-4140-8195-c32247ccb2af",
        ),
        ActorState(
            actor_id="4e07c27f63f95807cafe1ea701000000",
            class_name="ProgressTracker",
            state="ALIVE",
            job_id="01000000",
            name="",
            node_id="e227e86b72a0e9340c3eaec24cbdc2606830fc63b770583640205c95",
            pid=657553,
            ray_namespace="4490874b-64d4-4140-8195-c32247ccb2af",
        ),
        ActorState(
            actor_id="5e07c27f63f95807cafe1ea701000000",
            class_name="ApplierActor",
            state="PENDING_CREATION",
            job_id="01000000",
            name="",
            node_id="e227e86b72a0e9340c3eaec24cbdc2606830fc63b770583640205c95",
            pid=657554,
            ray_namespace="4490874b-64d4-4140-8195-c32247ccb2af",
        ),
        ActorState(
            actor_id="6e07c27f63f95807cafe1ea701000000",
            class_name="ApplierActor",
            state="DEPENDENCIES_UNREADY",
            job_id="01000000",
            name="",
            node_id="e227e86b72a0e9340c3eaec24cbdc2606830fc63b770583640205c95",
            pid=657553,
            ray_namespace="4490874b-64d4-4140-8195-c32247ccb2af",
        ),
        ActorState(
            actor_id="7e07c27f63f95807cafe1ea701000000",
            class_name="ApplierActor",
            state="RESTARTING",
            job_id="01000000",
            name="",
            node_id="e227e86b72a0e9340c3eaec24cbdc2606830fc63b770583640205c95",
            pid=657553,
            ray_namespace="4490874b-64d4-4140-8195-c32247ccb2af",
        ),
        ActorState(
            actor_id="8017a2c6bd91443240895bcd01000000",
            class_name="ProgressTracker",
            state="ALIVE",
            job_id="01000000",
            name="",
            node_id="e227e86b72a0e9340c3eaec24cbdc2606830fc63b770583640205c95",
            pid=657555,
            ray_namespace="4490874b-64d4-4140-8195-c32247ccb2af",
        ),
    ]


def test_ray_status_with_real_actorstate(monkeypatch) -> None:
    # stub cluster_resources
    monkeypatch.setattr(ray, "cluster_resources", lambda: {"CPU": 32, "GPU": 1})
    nodes = ast.literal_eval(ray_nodes_json)
    monkeypatch.setattr(ray, "nodes", lambda: nodes)
    monkeypatch.setattr(
        "geneva.runners.ray.kuberay.list_actors",
        lambda **kwargs: make_actor_states(),
        raising=True,
    )

    # run
    status = _ray_status()

    # only one live node in our JSON
    assert status["cnt_ray_nodes"] == 1
    assert status["cnt_geneva_workers_active"] == 1
    assert status["cnt_geneva_workers_pending"] == 3

    # no error field
    assert "error" not in status


def test_ray_status_with_real_actorstate_no_ray(monkeypatch) -> None:
    # stub cluster_resources
    def raise_exception(ex) -> None:
        """lambdas cannot directly raise exceptions"""
        raise ex

    monkeypatch.setattr(
        ray, "cluster_resources", lambda: raise_exception(Exception("not connected"))
    )

    # run
    status = _ray_status()

    # no  live nodes in our JSON
    assert status["cnt_ray_nodes"] == 0

    # error field
    assert "ray_nodes_error" in status


# Dummy classes to simulate Kubernetes pod objects
class DummyCondition:
    def __init__(self, _type: str, status: str) -> None:
        self.type = _type
        self.status = status


class DummyStatus:
    def __init__(self, phase: str, conditions: list[DummyCondition]) -> None:
        self.phase = phase
        self.conditions = conditions
        self.init_container_statuses = []
        self.container_statuses = []


class DummyMetadata:
    def __init__(self, name: str, labels: dict[str, str]) -> None:
        self.name = name
        self.labels = labels


class DummyPod:
    def __init__(
        self,
        name: str,
        labels: dict[str, str],
        phase: str,
        conditions: list[DummyCondition],
    ) -> None:
        self.metadata = DummyMetadata(name, labels)
        self.status = DummyStatus(phase, conditions)
        self.spec = None  # not used in the test


class DummyPodList:
    def __init__(self, items: list[DummyPod]) -> None:
        self.items = items


def test_k8s_status_filters_ray_pods_and_returns_details(monkeypatch) -> None:
    # Stub out kube_config.load_kube_config
    monkeypatch.setattr(kube_config, "load_kube_config", lambda: None)

    clients = KuberayClients(config_method=K8sConfigMethod.LOCAL)

    # Create a mix of pods, some with the ray label, some without
    pods = [
        DummyPod(
            name="ray-head-0",
            labels={"ray.io/node-type": "head"},
            phase="Running",
            conditions=[DummyCondition("Ready", "True")],
        ),
        DummyPod(
            name="other-pod",
            labels={},
            phase="Pending",
            conditions=[DummyCondition("Ready", "False")],
        ),
        DummyPod(
            name="ray-worker-1",
            labels={"ray.io/node-type": "worker"},
            phase="Pending",
            conditions=[DummyCondition("Ready", "False")],
        ),
    ]
    pod_list = DummyPodList(pods)

    # Stub out CoreV1Api.list_namespaced_pod
    class FakeCoreV1Api:
        def list_namespaced_pod(self, namespace) -> DummyPodList:
            assert namespace == "geneva"
            return pod_list

    monkeypatch.setattr(clients, "core_api", FakeCoreV1Api())

    # Call the function
    result = k8s_status(clients)

    # Verify that only the two ray pods are returned, in order
    assert len(result) == 2

    pod_statuses = [(r["name"], r["phase"], r["ready"]) for r in result]
    head_name, head_phase, head_ready = pod_statuses[0]
    assert head_name == "ray-head-0"
    assert head_phase == "Running"
    assert head_ready

    worker_name, worker_phase, worker_ready = pod_statuses[1]
    assert worker_name == "ray-worker-1"
    assert worker_phase == "Pending"
    assert not worker_ready


def test_k8s_status_returns_empty_when_no_ray_pods(monkeypatch) -> None:
    # Stub out kube_config.load_kube_config
    monkeypatch.setattr(kube_config, "load_kube_config", lambda: None)

    clients = KuberayClients(config_method=K8sConfigMethod.LOCAL)

    # Pod list with no ray.io/node-type labels
    pods = [
        DummyPod("app-1", {}, "Running", [DummyCondition("Ready", "True")]),
        DummyPod("app-2", {}, "Failed", [DummyCondition("Ready", "False")]),
    ]
    pod_list = DummyPodList(pods)

    class FakeCoreV1Api:
        def list_namespaced_pod(self, namespace) -> DummyPodList:
            assert namespace == "geneva"
            return pod_list

    monkeypatch.setattr(clients, "core_api", FakeCoreV1Api())

    result = k8s_status(clients)
    assert result == []  # no pods matching the ray label
