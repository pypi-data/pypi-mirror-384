import datetime
import json
import uuid
from typing import Any

import jsondiff
import pytest
from imecilabt.gpulab.schemas.job2 import (
    Job,
    JobEventTimes,
    JobOwner,
    JobOwnerV5,
    JobPortMapping,
    JobRequest,
    JobRequestDocker,
    JobRequestExtra,
    JobRequestResources,
    JobRequestScheduling,
    JobState,
    JobStateResources,
    JobStateScheduling,
    JobStatus,
    JobStorage,
    JobV5,
    MaxSimultaneousJobs,
    RestartInfo,
    TmpfsJobStorage,
)
from pydantic import TypeAdapter, ValidationError

from .test_usage_statistics import (
    TEST_GPU_OVERVIEW_JSON,
    TEST_GPU_OVERVIEW_OBJ,
    TEST_GPULAB_USAGE_STATISTICS_JSON,
    TEST_GPULAB_USAGE_STATISTICS_OBJ,
)

job_list_adapter = TypeAdapter(list[Job])


def _parse_date(date: str) -> datetime.datetime:
    return datetime.datetime.fromisoformat(date)


TEST_JOB2_REQUEST_RESOURCES_JSON = """{
  "cpus": 4,
  "gpus": 2,
  "cpuMemoryGb": 8,

  "minCudaVersion": 10,
  "clusterId": 7,
  "gpuModel": ["1080", "v100"],
  "slaveName": "slave4B",
  "slaveInstanceId": "inst10",
  "features": ["SHARED_PROJECT_STORAGE", "FAST_SCRATCH_PROJECT_STORAGE",
               "PUBLIC_IPV4", "PUBLIC_IPV6", "UNFIREWALLED_PORTS", "SSH_ACCESS"]
}"""


TEST_JOB2_REQUEST_RESOURCES_OBJ_A = JobRequestResources(
    cpus=4,
    gpus=2,
    cpu_memory_gb=8,
    gpu_memory_gb=None,
    min_cuda_version=10,
    cluster_id=7,
    gpu_model=["1080", "v100"],
    slave_name="slave4B",
    slave_instance_id="inst10",
    features=[
        "SHARED_PROJECT_STORAGE",
        "FAST_SCRATCH_PROJECT_STORAGE",
        "PUBLIC_IPV4",
        "PUBLIC_IPV6",
        "UNFIREWALLED_PORTS",
        "SSH_ACCESS",
    ],
)


def test_job2_request_resources_from_json() -> None:
    actual = JobRequestResources.model_validate_json(TEST_JOB2_REQUEST_RESOURCES_JSON)
    assert actual == TEST_JOB2_REQUEST_RESOURCES_OBJ_A

    assert json.loads(TEST_JOB2_REQUEST_RESOURCES_JSON) == actual.model_dump(by_alias=True, exclude_unset=True)


TEST_JOB2_REQUEST_SCHEDULING_JSON = """{
  "interactive": false,
  "minDuration": "5 hour",
  "restartable": false,
  "reservationIds": ["01993203-f43a-480c-b097-0d629f95d445"],

  "maxDuration": "5 hour",
  "maxSimultaneousJobs": {
    "bucketName": "my-3jobs-demo",
    "bucketMax": 3
  },
  "notBefore": "2020-03-17T05:00:13Z",
  "notAfter": "2020-03-17T18:00:13Z"
}"""

TEST_JOB2_REQUEST_SCHEDULING_OBJ_A = JobRequestScheduling(
    interactive=False,
    min_duration="5 hour",
    restartable=False,
    reservation_ids=["01993203-f43a-480c-b097-0d629f95d445"],
    max_duration="5 hour",
    max_simultaneous_jobs=MaxSimultaneousJobs(bucket_max=3, bucket_name="my-3jobs-demo"),
    not_before=_parse_date("2020-03-17T05:00:13Z"),
    not_after=_parse_date("2020-03-17T18:00:13Z"),
)

TEST_JOB2_REQUEST_SCHEDULING_OBJ_B = JobRequestScheduling(
    min_duration="5 hour",
    max_duration="5 hour",
)


def test_job2_request_scheduling_from_json() -> None:
    actual = JobRequestScheduling.model_validate_json(TEST_JOB2_REQUEST_SCHEDULING_JSON)
    assert actual == TEST_JOB2_REQUEST_SCHEDULING_OBJ_A
    assert jsondiff.diff(
        TEST_JOB2_REQUEST_SCHEDULING_JSON,
        actual.model_dump_json(by_alias=True),
        load=True,
    )


TEST_JOB2_REQUEST_SCHEDULING_SINGLE_RESERVATION_ID_JSON = """{
  "interactive": false,
  "minDuration": "5 hour",
  "restartable": false,
  "reservationId": "01993203-f43a-480c-b097-0d629f95d445",

  "maxDuration": "5 hour",
  "maxSimultaneousJobs": {
    "bucketName": "my-3jobs-demo",
    "bucketMax": 3
  },
  "notBefore": "2020-03-17T05:00:13Z",
  "notAfter": "2020-03-17T18:00:13Z"
}"""


def test_job2_request_scheduling_from_json_single_reservationid() -> None:
    actual = JobRequestScheduling.model_validate_json(TEST_JOB2_REQUEST_SCHEDULING_SINGLE_RESERVATION_ID_JSON)
    assert actual == TEST_JOB2_REQUEST_SCHEDULING_OBJ_A
    difference = jsondiff.diff(
        TEST_JOB2_REQUEST_SCHEDULING_SINGLE_RESERVATION_ID_JSON,
        actual.model_dump_json(by_alias=True, exclude_unset=True),
        load=True,
    )
    assert "reservationIds" in difference
    assert difference[jsondiff.delete] == ["reservationId"]


# minDuration was named killableAfter for a while!
TEST_JOB2_REQUEST_SCHEDULING_JSON_BACKWARD_COMP = """{
  "interactive": false,
  "killableAfter": "5 hour",
  "restartable": false,
  "reservationId": "01993203-f43a-480c-b097-0d629f95d445",

  "maxDuration": "5 hour",
  "maxSimultaneousJobs": {
    "bucketName": "my-3jobs-demo",
    "bucketMax": 3
  },
  "notBefore": "2020-03-17T05:00:13Z",
  "notAfter": "2020-03-17T18:00:13Z"
}"""


def test_job2_request_scheduling_backward_compat_from_json() -> None:
    actual = JobRequestScheduling.model_validate_json(TEST_JOB2_REQUEST_SCHEDULING_JSON_BACKWARD_COMP)
    assert actual == TEST_JOB2_REQUEST_SCHEDULING_OBJ_A
    difference = jsondiff.diff(
        TEST_JOB2_REQUEST_SCHEDULING_JSON_BACKWARD_COMP,
        actual.model_dump_json(by_alias=True, exclude_unset=True),
        load=True,
    )
    assert difference["reservationIds"] == ["01993203-f43a-480c-b097-0d629f95d445"]
    assert difference["minDuration"] == "5 hour"
    assert set(difference[jsondiff.delete]) == {"reservationId", "killableAfter"}


TEST_JOB2_REQUEST_DOCKER_JSON = """{
    "image":
    "gitlab.ilabt.imec.be:4567/ilabt/gpu-docker-stacks/tensorflow-notebook:83755206e3198b4914852bd640c102cb757fc02e",
    "command": [ "/project/start-demo.sh", "demo" ],
    "environment": {
      "MYDEMOENVVAR": "demo"
    },
    "storage": [
      {
        "containerPath": "/proj/",
        "hostPath": "/project/"
      },
      {
        "hostPath": "/project_scratch/"
      },
      {
        "containerPath": "/project_scratch2/"
      },
      {
        "containerPath": "/foobar/",
        "hostPath": "tmpfs",
        "sizeGb": 5
      }
    ],
    "portMappings": [
      {
        "containerPort": 8888,
        "hostPort": 80
      }
    ],

    "projectGidVariableName": "NB_GID",
    "user": "root",
    "groupAdd": ["demogroup"],
    "workingDir": "/root/"
}"""


TEST_JOB2_REQUEST_DOCKER_OBJ_A = JobRequestDocker(
    image="gitlab.ilabt.imec.be:4567/ilabt/gpu-docker-stacks/tensorflow-notebook:83755206e3198b4914852bd640c102cb757fc02e",
    command=["/project/start-demo.sh", "demo"],
    environment={"MYDEMOENVVAR": "demo"},
    project_gid_variable_name="NB_GID",
    user="root",
    group_add=["demogroup"],
    working_dir="/root/",
    storage=[
        JobStorage(container_path="/proj", host_path="/project"),
        JobStorage(container_path="/project_scratch", host_path="/project_scratch"),
        JobStorage(container_path="/project_scratch2", host_path="/project_scratch2"),
        TmpfsJobStorage(container_path="/foobar", host_path="tmpfs", size_gb=5),
    ],
    port_mappings=[JobPortMapping(container_port=8888, host_port=80)],
)


def test_job2_request_docker_from_json() -> None:
    actual = JobRequestDocker.model_validate_json(TEST_JOB2_REQUEST_DOCKER_JSON)
    assert actual == TEST_JOB2_REQUEST_DOCKER_OBJ_A

    assert not jsondiff.diff(
        TEST_JOB2_REQUEST_DOCKER_JSON,
        actual.model_dump_json(by_alias=True, exclude_unset=True),
        load=True,
    )


# Contains unnormalized paths.
TEST_JOB2_REQUEST_DOCKER_JSON_NOT_NORMALIZED = """{
    "image":
    "gitlab.ilabt.imec.be:4567/ilabt/gpu-docker-stacks/tensorflow-notebook:83755206e3198b4914852bd640c102cb757fc02e",
    "command": [ "/project/start-demo.sh", "demo" ],
    "environment": {
      "MYDEMOENVVAR": "demo"
    },
    "storage": [
      {
        "containerPath": "/proj",
        "hostPath": "/project"
      },
      {
        "hostPath": "/project_scratch"
      },
      {
        "containerPath": "/project_scratch2"
      },
      {
        "containerPath": "/foobar",
        "hostPath": "tmpfs",
        "sizeGb": 5
      }
    ],
    "portMappings": [
      {
        "containerPort": 8888,
        "hostPort": 80
      }
    ],

    "projectGidVariableName": "NB_GID",
    "user": "root",
    "groupAdd": ["demogroup"],
    "workingDir": "/root/"
}"""


def test_job2_request_docker_from_not_normalized_json() -> None:
    actual = JobRequestDocker.model_validate_json(TEST_JOB2_REQUEST_DOCKER_JSON_NOT_NORMALIZED)
    assert actual == TEST_JOB2_REQUEST_DOCKER_OBJ_A

    assert not jsondiff.diff(
        TEST_JOB2_REQUEST_DOCKER_JSON,
        actual.model_dump_json(by_alias=True, exclude_unset=True),
        load=True,
    )


TEST_JOB2_REQUEST_EXTRA_JSON = """{
   "sshPubKeys": ["ssh-rsa test1"],
   "emailOnEnd": ["end@example.com"],
   "emailOnQueue": ["queue1@example.com", "queue2@example.com"],
   "emailOnRun": ["run@example.com"],
   "emailOnHalt": ["halted@example.com"],
   "emailOnRestart": ["restart@example.com"]
}"""


TEST_JOB2_REQUEST_EXTRA_OBJ_A = JobRequestExtra(
    ssh_pub_keys=["ssh-rsa test1"],
    email_on_end=["end@example.com"],
    email_on_queue=["queue1@example.com", "queue2@example.com"],
    email_on_run=["run@example.com"],
    email_on_halt=["halted@example.com"],
    email_on_restart=["restart@example.com"],
)


def test_job2_extra_from_json() -> None:
    actual = JobRequestExtra.model_validate_json(TEST_JOB2_REQUEST_EXTRA_JSON)
    assert actual == TEST_JOB2_REQUEST_EXTRA_OBJ_A
    assert not jsondiff.diff(TEST_JOB2_REQUEST_EXTRA_JSON, actual.model_dump_json(by_alias=True), load=True)


TEST_JOB2_REQUEST_JSON = (
    """{
    "resources": """
    + TEST_JOB2_REQUEST_RESOURCES_JSON
    + """,
    "scheduling": """
    + TEST_JOB2_REQUEST_SCHEDULING_JSON
    + """,
    "docker": """
    + TEST_JOB2_REQUEST_DOCKER_JSON
    + """,
    "extra": """
    + TEST_JOB2_REQUEST_EXTRA_JSON
    + """
}"""
)


def test_job2_request_from_json() -> None:
    actual = JobRequest.model_validate_json(TEST_JOB2_REQUEST_JSON)
    assert actual == TEST_JOB2_REQUEST_OBJ_A
    actual_json = actual.model_dump_json(by_alias=True, exclude_unset=True)
    assert not jsondiff.diff(
        TEST_JOB2_REQUEST_JSON,
        actual_json,
        load=True,
    )


TEST_JOB2_REQUEST_JSON_BACKWARD_COMP = (
    """{
    "resources": """
    + TEST_JOB2_REQUEST_RESOURCES_JSON
    + """,
    "scheduling": """
    + TEST_JOB2_REQUEST_SCHEDULING_JSON_BACKWARD_COMP
    + """,
    "docker": """
    + TEST_JOB2_REQUEST_DOCKER_JSON
    + """,
    "extra": """
    + TEST_JOB2_REQUEST_EXTRA_JSON
    + """
}"""
)

TEST_JOB2_REQUEST_RESOURCES_OBJ_B = JobRequestResources(
    cpus=1,
    gpus=0,
    cpu_memory_gb=4,
    gpu_memory_gb=4,
    min_cuda_version=None,
    cluster_id=None,
)


TEST_JOB2_REQUEST_DOCKER_OBJ_B = JobRequestDocker(image="debian:stable")

TEST_JOB2_REQUEST_OBJ_A = JobRequest(
    resources=TEST_JOB2_REQUEST_RESOURCES_OBJ_A,
    scheduling=TEST_JOB2_REQUEST_SCHEDULING_OBJ_A,
    docker=TEST_JOB2_REQUEST_DOCKER_OBJ_A,
    extra=TEST_JOB2_REQUEST_EXTRA_OBJ_A,
)
TEST_JOB2_REQUEST_OBJ_B = JobRequest(
    resources=TEST_JOB2_REQUEST_RESOURCES_OBJ_B,
    scheduling=TEST_JOB2_REQUEST_SCHEDULING_OBJ_B,
    docker=TEST_JOB2_REQUEST_DOCKER_OBJ_B,
)


def test_job2_request_from_json_backward_comp() -> None:
    actual = JobRequest.model_validate_json(TEST_JOB2_REQUEST_JSON_BACKWARD_COMP)
    assert actual == TEST_JOB2_REQUEST_OBJ_A

    assert not jsondiff.diff(
        TEST_JOB2_REQUEST_JSON,
        actual.model_dump_json(by_alias=True, exclude_unset=True),
        load=True,
    )


def test_job2_request_docker_from_json1() -> None:
    in_json = """{
            "image": "dummy",
            "command": "test direct string",
            "groupAdd": "demogroup"
        }
    """
    out_job2_request_docker: JobRequestDocker = JobRequestDocker.model_validate_json(in_json)

    assert out_job2_request_docker == JobRequestDocker(
        image="dummy",
        command="test direct string",
        environment={},
        project_gid_variable_name=None,
        user=None,
        group_add=["demogroup"],
        working_dir=None,
        storage=[],
        port_mappings=[],
    )


def test_job2_request_docker_from_json2() -> None:
    in_json = """{
            "image": "dummy",
            "storage": [
              "/project_scratch",
              {
                "containerPath": "/proj",
                "hostPath": "/project"
              },
              "/project_scratch2",
              {
                "containerPath": "/baz",
                "hostPath": "tmpfs",
                "sizeGb": 4
              }
            ],
            "portMappings": [
              77,
              {
                "containerPort": 8888,
                "hostPort": 80
              }
            ]
        }
    """
    out_job2_request_docker: JobRequestDocker = JobRequestDocker.model_validate_json(in_json)

    assert out_job2_request_docker == JobRequestDocker(
        image="dummy",
        command=[],
        environment={},
        project_gid_variable_name=None,
        user=None,
        group_add=[],
        working_dir=None,
        storage=[
            JobStorage(container_path="/project_scratch", host_path="/project_scratch"),
            JobStorage(container_path="/proj", host_path="/project"),
            JobStorage(container_path="/project_scratch2", host_path="/project_scratch2"),
            TmpfsJobStorage(container_path="/baz", host_path="tmpfs", size_gb=4),
        ],
        port_mappings=[
            JobPortMapping(container_port=77, host_port=None),
            JobPortMapping(container_port=8888, host_port=80),
        ],
    )


TEST_JOB2_STATE_RESOURCES_JSON = (
    """{
   "clusterId": 7,
   "cpuIds": [4, 5],
   "gpuIds": [1],
   "cpuMemoryGb": 8,
   "gpuMemoryGb": 4,

   "slaveHost": "hostname.example.com",
   "slaveName": "hostname",
   "slaveInstanceId": "inst8",
   "slaveInstancePid": 5097,
   "workerId": 11,

   "sshHost": "host.example.com",
   "sshPort": 22,
   "sshUsername": "ABCDEF",
   "sshProxyHost": "bastion.example.com",
   "sshProxyPort": 2222,
   "sshProxyUsername": "fffdemo",

   "gpuDetails": """
    + TEST_GPU_OVERVIEW_JSON
    + """,
   "portMappings": [
     {
       "containerPort": 8888,
       "hostIp": "0.0.0.0",
       "hostPort": 32935
     }
   ]
 }"""
)


TEST_JOB2_STATE_RESOURCES_OBJ_A = JobStateResources(
    cluster_id=7,
    cpu_ids=[4, 5],
    gpu_ids=[1],
    cpu_memory_gb=8,
    gpu_memory_gb=4,
    slave_host="hostname.example.com",
    slave_name="hostname",
    slave_instance_id="inst8",
    slave_instance_pid=5097,
    worker_id=11,
    ssh_host="host.example.com",
    ssh_port=22,
    ssh_username="ABCDEF",
    ssh_proxy_host="bastion.example.com",
    ssh_proxy_port=2222,
    ssh_proxy_username="fffdemo",
    port_mappings=[
        JobPortMapping(container_port=8888, host_ip="0.0.0.0", host_port=32935)  # noqa: S104
    ],  # noqa: S104
    gpu_details=TEST_GPU_OVERVIEW_OBJ,
    tmpfs_mem_gb=0,
)


def test_job2_state_resources_from_json() -> None:
    actual = JobStateResources.model_validate_json(TEST_JOB2_STATE_RESOURCES_JSON)
    assert actual == TEST_JOB2_STATE_RESOURCES_OBJ_A


TEST_JOB2_STATE_EVENTTIMES_JSON = """{
   "created": "2020-03-17T09:59:19Z",
   "statusUpdated": "2020-03-17T10:00:13Z",

   "QUEUED": "2020-03-17T09:59:20Z",
   "ASSIGNED": "2020-03-17T08:59:24Z",
   "STARTING": "2020-03-17T09:59:21Z",
   "RUNNING": "2020-03-17T09:59:22Z",
   "FINISHED": "2020-03-17T09:59:23Z",
   "FAILED": "2020-03-17T09:59:24Z",
   "CANCELLED": "2020-03-17T09:59:25Z",
   "DELETED": "2020-03-17T09:59:26Z",
   "longRunNotify": "2020-03-18T09:59:21Z",
    "MUSTHALT": "2020-03-17T09:59:27Z",
    "HALTING": "2020-03-17T09:59:28Z",
    "HALTED": "2020-03-17T09:59:29Z"
 }"""

TEST_JOB2_STATE_EVENTTIMES_OBJ_A = JobEventTimes(
    created=_parse_date("2020-03-17T09:59:19Z"),
    status_updated=_parse_date("2020-03-17T10:00:13Z"),
    QUEUED=_parse_date("2020-03-17T09:59:20Z"),
    ASSIGNED=_parse_date("2020-03-17T08:59:24Z"),
    STARTING=_parse_date("2020-03-17T09:59:21Z"),
    RUNNING=_parse_date("2020-03-17T09:59:22Z"),
    FINISHED=_parse_date("2020-03-17T09:59:23Z"),
    FAILED=_parse_date("2020-03-17T09:59:24Z"),
    CANCELLED=_parse_date("2020-03-17T09:59:25Z"),
    DELETED=_parse_date("2020-03-17T09:59:26Z"),
    MUSTHALT=_parse_date("2020-03-17T09:59:27Z"),
    HALTING=_parse_date("2020-03-17T09:59:28Z"),
    HALTED=_parse_date("2020-03-17T09:59:29Z"),
    long_run_notify=_parse_date("2020-03-18T09:59:21Z"),
)


def test_job2_state_eventtimes_from_json() -> None:
    actual = JobEventTimes.model_validate_json(TEST_JOB2_STATE_EVENTTIMES_JSON)
    assert actual == TEST_JOB2_STATE_EVENTTIMES_OBJ_A

    assert not jsondiff.diff(
        TEST_JOB2_STATE_EVENTTIMES_JSON,
        actual.model_dump_json(by_alias=True, exclude_unset=True),
        load=True,
    )


TEST_JOB2_STATE_SCHEDULING_JSON = """{
   "assignedClusterId": 7,
   "assignedInstanceId": "inst8",
   "assignedSlaveName": "hostname",
   "queuedExplanations": [],
   "tallyIncrement": 123.4
}"""


TEST_JOB2_STATE_SCHEDULING_OBJ_A = JobStateScheduling(
    assigned_cluster_id=7,
    assigned_instance_id="inst8",
    assigned_slave_name="hostname",
    queued_explanations=[],
    tally_increment=123.4,
)


def test_job2_state_scheduling_from_json() -> None:
    actual = JobStateScheduling.model_validate_json(TEST_JOB2_STATE_SCHEDULING_JSON)
    assert actual == TEST_JOB2_STATE_SCHEDULING_OBJ_A

    assert not jsondiff.diff(
        TEST_JOB2_STATE_SCHEDULING_JSON,
        actual.model_dump_json(by_alias=True, exclude_unset=True),
        load=True,
    )


# contains deprecated 'withinMaxSimultaneousJobs'
TEST_JOB2_STATE_SCHEDULING_JSON_BACKWARD_COMPAT = """{
   "assignedClusterId": 7,
   "assignedInstanceId": "inst8",
   "assignedSlaveName": "hostname",
   "queuedExplanations": [],
   "withinMaxSimultaneousJobs": true,
   "tallyIncrement": 123.4
}"""

TEST_JOB2_STATE_SCHEDULING_OBJ_BACKWARD_COMPAT = JobStateScheduling(
    assigned_cluster_id=7,
    assigned_instance_id="inst8",
    assigned_slave_name="hostname",
    queued_explanations=[],
    within_max_simultaneous_jobs=True,
    tally_increment=123.4,
)


def test_job2_state_scheduling_from_json_backward_compat() -> None:
    actual = JobStateScheduling.model_validate_json(TEST_JOB2_STATE_SCHEDULING_JSON_BACKWARD_COMPAT)
    assert actual == TEST_JOB2_STATE_SCHEDULING_OBJ_BACKWARD_COMPAT

    assert not jsondiff.diff(
        TEST_JOB2_STATE_SCHEDULING_JSON,
        actual.model_dump_json(by_alias=True, exclude_unset=True),
        load=True,
    )


TEST_JOB2_STATE_JSON = (
    """{
     "status": "RUNNING",
     "resources": """
    + TEST_JOB2_STATE_RESOURCES_JSON
    + """,
     "eventTimes": """
    + TEST_JOB2_STATE_EVENTTIMES_JSON
    + """,
     "scheduling": """
    + TEST_JOB2_STATE_SCHEDULING_JSON
    + """,
     "finalUsageStatistics": """
    + TEST_GPULAB_USAGE_STATISTICS_JSON
    + """
}"""
)

TEST_JOB2_STATE_OBJ_A = JobState(
    status=JobStatus.RUNNING,
    resources=TEST_JOB2_STATE_RESOURCES_OBJ_A,
    scheduling=TEST_JOB2_STATE_SCHEDULING_OBJ_A,
    event_times=TEST_JOB2_STATE_EVENTTIMES_OBJ_A,
    final_usage_statistics=TEST_GPULAB_USAGE_STATISTICS_OBJ,
)


def test_job2_state_from_json() -> None:
    out_job2_state: JobState = JobState.model_validate_json(TEST_JOB2_STATE_JSON)
    assert out_job2_state == TEST_JOB2_STATE_OBJ_A
    assert not jsondiff.diff(
        TEST_JOB2_STATE_JSON,
        out_job2_state.model_dump_json(by_alias=True, exclude_none=True, exclude_unset=True),
        load=True,
    )


TEST_JOB2_STATE_SCHEDULING_OBJ_B = JobStateScheduling(
    queued_explanations=["Not enough free resources too run this Job"]
)


TEST_JOB2_STATE_EVENTTIMES_OBJ_B = JobEventTimes(
    created=_parse_date("2020-04-15T09:59:19Z"),
    status_updated=_parse_date("2020-04-15T12:34:56Z"),
    QUEUED=_parse_date("2020-04-15T09:59:20Z"),
)


TEST_JOB2_STATE_OBJ_B = JobState(
    status=JobStatus.QUEUED,
    resources=None,
    scheduling=TEST_JOB2_STATE_SCHEDULING_OBJ_B,
    event_times=TEST_JOB2_STATE_EVENTTIMES_OBJ_B,
    final_usage_statistics=None,
)


TEST_JOB2_OWNER_JSON = """{
    "userUrn": "urn:publicid:IDN+example.com+user+tester",
    "userEmail": "tester@example.com",
    "projectUrn": "urn:publicid:IDN+example.com+project+testproj"
}"""

TEST_JOB2_OWNER_OBJ_A = JobOwner(
    user_urn="urn:publicid:IDN+example.com+user+tester",
    user_email="tester@example.com",
    project_urn="urn:publicid:IDN+example.com+project+testproj",
)

TEST_JOB2_OWNER_OBJ_A_SANITIZED = JobOwner(
    user_urn="urn:publicid:IDN+hidden+user+hidden",
    user_email="hidden@hidden.hidden",
    project_urn="urn:publicid:IDN+hidden+project+hidden",
)

TEST_JOB2_OWNER_OBJ_A_V5 = JobOwnerV5(
    user_id="user_example.com_00112233445566hegtavwyanz1",
    project_id="proj_example.com_00112233445566hegtavwyanz2",
    experiment_id="exp_example.com_00112233445566hegtavwyanz3",
)


def test_job_owner1() -> None:
    actual = JobOwner.model_validate_json(TEST_JOB2_OWNER_JSON)
    assert actual == TEST_JOB2_OWNER_OBJ_A

    assert not jsondiff.diff(
        TEST_JOB2_OWNER_JSON,
        actual.model_dump_json(by_alias=True, exclude_unset=True),
        load=True,
    )


TEST_JOB2_OWNER_OBJ_B = JobOwner(
    user_urn="urn:publicid:IDN+example.com+user+testerB",
    user_email="testerB@example.com",
    project_urn="urn:publicid:IDN+example.com+project+testprojB",
)


TEST_JOB2_UUID_A = str(uuid.uuid4())
TEST_JOB2_UUID_B = "0ae7f528-ac52-4362-8d2f-ab6756977a1c"
TEST_JOB2_UUID_NEW = str(uuid.uuid4())
TEST_JOB2_UUID_B_2 = "0a49e527-8e86-4803-9162-ed6509206baf"
TEST_JOB2_UUID_B_5 = "0ae7f61f-c617-46a9-bbb0-060041ab537c"


# TEST_JOB2_JSON = (
#     """{
#     "uuid": """
#     + '"'
#     + TEST_JOB2_UUID_A
#     + '"'
#     + """,
#     "name": "testJobA",
#     "deploymentEnvironment": "production",
#     "request": """
#     + TEST_JOB2_REQUEST_JSON
#     + """,
#     "description": "Test Job A",
#     "owner": """
#     + TEST_JOB2_OWNER_JSON
#     + """,
#     "state": """
#     + TEST_JOB2_STATE_JSON
#     + """
# }"""
# )
TEST_JOB2_JSON = (
    "{"
    f"""
    "uuid": "{TEST_JOB2_UUID_A}",
    "name": "testJobA",
    "deploymentEnvironment": "production",
    "request": {TEST_JOB2_REQUEST_JSON},
    "description": "Test Job A",
    "owner": {TEST_JOB2_OWNER_JSON},
    "state": {TEST_JOB2_STATE_JSON}
    """
    "}"
)

TEST_JOB2_OBJ_A = Job(
    id=TEST_JOB2_UUID_A,
    name="testJobA",
    deployment_environment="production",
    request=TEST_JOB2_REQUEST_OBJ_A,
    description="Test Job A",
    owner=TEST_JOB2_OWNER_OBJ_A,
    state=TEST_JOB2_STATE_OBJ_A,
)

TEST_JOB2_OBJ_A_SANITIZED = Job(
    id=TEST_JOB2_UUID_A,
    name=f"job-{TEST_JOB2_UUID_A[:6]}",
    deployment_environment="production",
    request=TEST_JOB2_REQUEST_OBJ_A.sanitized_copy(logged_in=True, same_project=False),
    description=None,
    owner=TEST_JOB2_OWNER_OBJ_A_SANITIZED,
    state=TEST_JOB2_STATE_OBJ_A.sanitized_copy(logged_in=True, same_project=False),
)

TEST_JOB2_OBJ_A_V5 = JobV5(
    id=TEST_JOB2_UUID_A,
    name="testJobA",
    deployment_environment="production",
    request=TEST_JOB2_REQUEST_OBJ_A,
    description="Test Job A",
    owner=TEST_JOB2_OWNER_OBJ_A_V5,
    state=TEST_JOB2_STATE_OBJ_A,
)


def test_job_a() -> None:
    actual = Job.model_validate_json(TEST_JOB2_JSON)
    assert actual == TEST_JOB2_OBJ_A
    assert not jsondiff.diff(
        TEST_JOB2_JSON,
        actual.model_dump_json(by_alias=True, exclude_unset=True, exclude_none=True),
        load=True,
    )


TEST_JOB2_JSON_BACKWARD_COMP = (
    "{"
    f"""
    "uuid": "{TEST_JOB2_UUID_A}",
    "name": "testJobA",
    "deploymentEnvironment": "production",
    "request": {TEST_JOB2_REQUEST_JSON_BACKWARD_COMP},
    "description": "Test Job A",
    "owner": {TEST_JOB2_OWNER_JSON},
    "state": {TEST_JOB2_STATE_JSON}
    """
    "}"
)


def test_job_a_backward_comp() -> None:
    actual = Job.model_validate_json(TEST_JOB2_JSON_BACKWARD_COMP)
    assert actual == TEST_JOB2_OBJ_A
    diff = jsondiff.diff(
        TEST_JOB2_JSON,
        actual.model_dump_json(by_alias=True, exclude_unset=True, exclude_none=True),
        load=True,
    )

    assert not diff


TEST_JOB2_OBJ_B = Job(
    id=TEST_JOB2_UUID_B,
    name="TestJobB",
    deployment_environment="production",
    request=TEST_JOB2_REQUEST_OBJ_B,
    description="Test Job B",
    owner=TEST_JOB2_OWNER_OBJ_B,
    state=TEST_JOB2_STATE_OBJ_B,
)

TEST_JOB2_JSON_B = TEST_JOB2_OBJ_B.model_dump_json(by_alias=True)

TEST_JOB2_OBJ_C: Job = TEST_JOB2_OBJ_A.model_copy(
    update={
        "id": "7287c5dd-715e-487e-887d-2a2c8e52651a",
        "name": "TestJobC",
        "owner": TEST_JOB2_OBJ_A.owner.model_copy(update={"user_urn": "urn:publicid:IDN+example.com+user+testerC"}),
        "state": TEST_JOB2_STATE_OBJ_A.model_copy(
            update={
                "resources": TEST_JOB2_STATE_RESOURCES_OBJ_A.model_copy(
                    update={
                        "slave_name": "hostnameB",
                        "slave_instance_id": "inst8",
                    }
                )
            }
        ),
    },
    deep=True,
)

# TEST_JOB2_JSON_C = TEST_JOB2_OBJ_C.model_dump_json(by_alias=True)  # Not used, causes serialization error


def test_job_a_to_from_json() -> None:
    expected = TEST_JOB2_OBJ_A
    actual = Job.model_validate_json(TEST_JOB2_OBJ_A.model_dump_json(by_alias=True))
    assert actual == expected


def test_job_a_to_from_dict() -> None:
    d = TEST_JOB2_OBJ_A.model_dump(mode="json", by_alias=True)
    actual = Job.model_validate(d)
    assert actual == TEST_JOB2_OBJ_A


def test_jobs_from_dict_1() -> None:
    input: list[dict[str, Any]] = []
    expected: list[Job] = []
    actual: list[Job] = job_list_adapter.validate_python(input)
    assert actual == expected


def test_jobs_from_dict_2() -> None:
    input = [TEST_JOB2_OBJ_A.model_dump(mode="json", by_alias=True)]
    actual: list[Job] = job_list_adapter.validate_python(input)
    assert actual == [TEST_JOB2_OBJ_A]


def test_job_a_to_dict_eventtimes() -> None:
    actual_dict = TEST_JOB2_OBJ_A.model_dump(mode="json", by_alias=True)
    assert "QUEUED" in actual_dict["state"]["eventTimes"]
    assert isinstance(actual_dict["state"]["eventTimes"]["QUEUED"], str)
    assert datetime.datetime.fromisoformat(
        actual_dict["state"]["eventTimes"]["QUEUED"]
    ) == datetime.datetime.fromisoformat("2020-03-17T09:59:20Z")


def test_job_from_json_valid_owner_check1() -> None:
    in_json = (
        "{"
        f"""
        "uuid": "{TEST_JOB2_UUID_A}",
        "state": {TEST_JOB2_STATE_JSON},
        """
        """
       "name": "check",
       "deploymentEnvironment": "staging",
       "request": {
          "docker": { "command":"nvidia-smi", "image":"nvidia/cuda:10.1-cudnn7-devel-ubuntu18.04"},
          "resources": { "clusterId":1,"cpus":1,"gpus":1,"cpuMemoryGb":2 },
          "scheduling": {
             "minDuration": "5 hour",
             "maxDuration": "5 hour"
          }
       },
       "owner": {
          "projectUrn": "urn:publicid:IDN+example.com+project+good",
          "userUrn": "urn:publicid:IDN+example.com+user+good",
          "userEmail": "good@example.com"
       }
    }"""
    )
    actual = Job.model_validate_json(in_json)
    assert actual.owner.project_urn == "urn:publicid:IDN+example.com+project+good"
    assert actual.owner.user_urn == "urn:publicid:IDN+example.com+user+good"
    assert actual.owner.user_email == "good@example.com"


def test_job_from_json_valid_owner_checkfail1() -> None:
    in_json = (
        "{"
        f"""
        "uuid": "{TEST_JOB2_UUID_A}",
        "state": {TEST_JOB2_STATE_JSON},
        """
        """
       "name": "check",
       "deploymentEnvironment": "staging",
       "request": {
          "docker": { "command":"nvidia-smi", "image":"nvidia/cuda:10.1-cudnn7-devel-ubuntu18.04"},
          "resources": { "clusterId":1,"cpus":1,"gpus":1,"cpuMemoryGb":2 }
       },
       "owner": {
          "projectUrn": "bad",
          "userUrn": "urn:publicid:IDN+example.com+user+good",
          "userEmail": "good@example.com"
       }
    }"""
    )
    with pytest.raises(ValidationError):
        Job.model_validate_json(in_json)


def test_job_from_json_valid_owner_checkfail2() -> None:
    in_json = (
        "{"
        f"""
        "id": "{TEST_JOB2_UUID_A}",
        "state": {TEST_JOB2_STATE_JSON},
        """
        """
       "name": "check",
       "deploymentEnvironment": "staging",
       "request": {
          "docker": { "command":"nvidia-smi", "image":"nvidia/cuda:10.1-cudnn7-devel-ubuntu18.04"},
          "resources": { "clusterId":1,"cpus":1,"gpus":1,"cpuMemoryGb":2 }
       },
       "owner": {
          "projectUrn": "urn:publicid:IDN+example.com+project+good",
          "userUrn": "bad",
          "userEmail": "good@example.com"
       }
    }"""
    )
    with pytest.raises(ValidationError):
        Job.model_validate_json(in_json)


def test_job_from_json_valid_owner_checkfail3() -> None:
    in_json = (
        "{"
        f"""
        "id": "{TEST_JOB2_UUID_A}",
        "state": {TEST_JOB2_STATE_JSON},
        """
        """
       "name": "check",
       "deploymentEnvironment": "staging",
       "request": {
          "docker": { "command":"nvidia-smi", "image":"nvidia/cuda:10.1-cudnn7-devel-ubuntu18.04"},
          "resources": { "clusterId":1,"cpus":1,"gpus":1,"cpuMemoryGb":2 }
       },
       "owner": {
          "projectUrn": "urn:publicid:IDN+example.com+project+good",
          "userUrn": "urn:publicid:IDN+example.com+user+good",
          "userEmail": "bad"
       }
    }"""
    )
    with pytest.raises(ValidationError):
        Job.model_validate_json(in_json)


def test_job_from_json_valid_owner_checkfail4() -> None:
    in_json = (
        "{"
        f"""
        "id": "{TEST_JOB2_UUID_A}",
        "state": {TEST_JOB2_STATE_JSON},
        """
        """
       "name": "check",
       "deploymentEnvironment": "staging",
       "request": {
          "docker": { "command":"nvidia-smi", "image":"nvidia/cuda:10.1-cudnn7-devel-ubuntu18.04"},
          "resources": { "clusterId":1,"cpus":1,"gpus":1,"cpuMemoryGb":2 }
       },
       "owner": {
          "projectUrn": "urn:publicid:IDN+example.com+project+good",
          "userUrn": "urn:publicid:IDN+example.com+bad+good",
          "userEmail": "good@example.com"
       }
    }"""
    )
    with pytest.raises(ValidationError):
        Job.model_validate_json(in_json)


def test_job_from_json_valid_owner_checkfail5() -> None:
    in_json = (
        "{"
        f"""
        "id": "{TEST_JOB2_UUID_A}",
        "state": {TEST_JOB2_STATE_JSON},
        """
        """
       "name": "check",
       "deploymentEnvironment": "staging",
       "request": {
          "docker": { "command":"nvidia-smi", "image":"nvidia/cuda:10.1-cudnn7-devel-ubuntu18.04"},
          "resources": { "clusterId":1,"cpus":1,"gpus":1,"cpuMemoryGb":2 }
       },
       "owner": {
          "projectUrn": "urn:publicid:IDN+example.com+bad+good",
          "userUrn": "urn:publicid:IDN+example.com+user+good",
          "userEmail": "good@example.com"
       }
    }"""
    )
    with pytest.raises(ValidationError):
        Job.model_validate_json(in_json)


def test_port_mapping_from_docker_dict_a() -> None:
    d = {"8888/tcp": [{"HostIp": "0.0.0.0", "HostPort": "32769"}]}  # noqa: S104
    container_port = "8888/tcp"
    actual = JobPortMapping.from_docker_dict(d[container_port][0], container_port=container_port)
    assert actual.host_port == 32769
    assert actual.container_port == 8888
    assert actual.host_ip == "0.0.0.0"  # noqa: S104


def test_port_mapping_from_docker_dict_b() -> None:
    d = {"HostIp": "127.0.0.1", "HostPort": "1111/tcp", "ContainerPort": "12345/udp"}
    actual = JobPortMapping.from_docker_dict(d)
    assert actual.host_port == 1111
    assert actual.container_port == 12345
    assert actual.host_ip == "127.0.0.1"


def test_matches_gpu_model_1() -> None:
    reqResources = JobRequestResources(
        cpus=1,
        gpus=1,
        cpu_memory_gb=1,
        gpu_model=["1080", "blah"],
        gpu_memory_gb=None,
        cluster_id=None,
        min_cuda_version=None,
    )
    assert reqResources.matches_gpu_model("nvidia GeForce 1080")
    assert reqResources.matches_gpu_model("1080 GeForce")
    assert reqResources.matches_gpu_model("a b1080c dd")
    assert reqResources.matches_gpu_model("1080")
    assert not reqResources.matches_gpu_model("108")
    assert reqResources.matches_gpu_model("blah")
    assert reqResources.matches_gpu_model("foo blah bar")
    assert reqResources.matches_gpu_model("BLAH")
    assert reqResources.matches_gpu_model("fooBLAHbar")
    assert reqResources.matches_gpu_model("bLAh")
    assert reqResources.matches_gpu_model("bLaHbLaHbLaH")


def test_matches_gpu_model_2() -> None:
    reqResources = JobRequestResources(
        cpus=1,
        gpus=1,
        cpu_memory_gb=1,
        gpu_model=["blah"],
        gpu_memory_gb=None,
        cluster_id=None,
        min_cuda_version=None,
    )
    assert not reqResources.matches_gpu_model("nvidia GeForce 1080")
    assert not reqResources.matches_gpu_model("1080 GeForce")
    assert not reqResources.matches_gpu_model("a b1080c dd")
    assert not reqResources.matches_gpu_model("1080")
    assert not reqResources.matches_gpu_model("108")
    assert reqResources.matches_gpu_model("blah")
    assert reqResources.matches_gpu_model("foo blah bar")
    assert reqResources.matches_gpu_model("BLAH")
    assert reqResources.matches_gpu_model("fooBLAHbar")
    assert reqResources.matches_gpu_model("bLAh")
    assert reqResources.matches_gpu_model("bLaHbLaHbLaH")


def test_matches_gpu_model_3() -> None:
    reqResources = JobRequestResources(
        cpus=1,
        gpus=1,
        cpu_memory_gb=1,
        gpu_model=[],
        gpu_memory_gb=None,
        cluster_id=None,
        min_cuda_version=None,
    )
    assert not reqResources.matches_gpu_model("nvidia GeForce 1080")
    assert not reqResources.matches_gpu_model("1080 GeForce")
    assert not reqResources.matches_gpu_model("a b1080c dd")
    assert not reqResources.matches_gpu_model("1080")
    assert not reqResources.matches_gpu_model("108")
    assert not reqResources.matches_gpu_model("blah")
    assert not reqResources.matches_gpu_model("foo blah bar")
    assert not reqResources.matches_gpu_model("BLAH")
    assert not reqResources.matches_gpu_model("fooBLAHbar")
    assert not reqResources.matches_gpu_model("bLAh")
    assert not reqResources.matches_gpu_model("bLaHbLaHbLaH")


def test_matches_gpu_model_4() -> None:
    def req_resources(req_model: str) -> JobRequestResources:
        return JobRequestResources(
            cpus=1,
            gpus=1,
            cpu_memory_gb=1,
            gpu_model=[req_model],
            gpu_memory_gb=None,
            cluster_id=None,
            min_cuda_version=None,
        )

    assert req_resources("A100").matches_gpu_model("NVIDIA A100 80GB PCIe (80 GB Mem)")
    assert req_resources("a100").matches_gpu_model("NVIDIA A100 80GB PCIe (80 GB Mem)")
    assert req_resources("A100 80GB").matches_gpu_model("NVIDIA A100 80GB PCIe (80 GB Mem)")
    assert req_resources("a100 80").matches_gpu_model("NVIDIA A100 80GB PCIe (80 GB Mem)")
    assert req_resources("(80 GB Mem)").matches_gpu_model("NVIDIA A100 80GB PCIe (80 GB Mem)")
    assert req_resources("(80 GB MEM)").matches_gpu_model("NVIDIA A100 80GB PCIe (80 GB Mem)")
    assert req_resources("NVIDIA A100 80GB PCIe (80 GB Mem)").matches_gpu_model("NVIDIA A100 80GB PCIe (80 GB Mem)")
    assert req_resources("nvidia a100 80gb pcie (80 gb mem)").matches_gpu_model("NVIDIA A100 80GB PCIe (80 GB Mem)")
    assert not req_resources(" NVIDIA A100 80gb PCIe (80 GB Mem)").matches_gpu_model(
        "NVIDIA A100 80GB PCIe (80 GB Mem)"
    )
    assert not req_resources("nvidia a100 80gb pcie (80 gb mem) ").matches_gpu_model(
        "NVIDIA A100 80GB PCIe (80 GB Mem)"
    )


def test_docker_request_group_add_json1() -> None:
    json_in = TEST_JOB2_REQUEST_DOCKER_JSON
    req_dock = JobRequestDocker.model_validate_json(json_in)
    assert req_dock.group_add == ["demogroup"]
    assert req_dock == TEST_JOB2_OBJ_A.request.docker


def test_docker_request_group_add_json2() -> None:
    # should also support json/dict with single string instead of list
    json_in = TEST_JOB2_REQUEST_DOCKER_JSON.replace('["demogroup"]', '"demogroup"')
    req_dock = JobRequestDocker.model_validate_json(json_in)
    assert req_dock.group_add == ["demogroup"]
    assert req_dock == TEST_JOB2_OBJ_A.request.docker


def test_docker_request_group_add_dict1() -> None:
    dict_in = TEST_JOB2_OBJ_A.request.docker.model_dump(mode="json", by_alias=True)
    dict_in["groupAdd"] = ["demogroup"]
    req_dock = JobRequestDocker.model_validate(dict_in)
    assert req_dock.group_add == ["demogroup"]
    assert req_dock == TEST_JOB2_OBJ_A.request.docker


def test_docker_request_group_add_dict2() -> None:
    # should also support json/dict with single string instead of list
    dict_in = TEST_JOB2_OBJ_A.request.docker.model_dump(mode="json", by_alias=True)
    dict_in["groupAdd"] = "demogroup"
    req_dock = JobRequestDocker.model_validate(dict_in)
    assert req_dock.group_add == ["demogroup"]
    assert req_dock == TEST_JOB2_OBJ_A.request.docker


def test_resource_request_gpu_model_dict1() -> None:
    dict_in = TEST_JOB2_OBJ_A.request.resources.model_dump(mode="json", by_alias=True)
    dict_in["gpuModel"] = ["TITAN"]
    req_resources = JobRequestResources.model_validate(dict_in)
    assert req_resources.gpu_model == ["TITAN"]
    assert req_resources == TEST_JOB2_OBJ_A.request.resources.model_copy(update={"gpu_model": ["TITAN"]})


def test_resource_request_gpu_model_dict2a() -> None:
    dict_in = TEST_JOB2_OBJ_A.request.resources.model_dump(mode="json", by_alias=True)
    dict_in["gpuModel"] = "TITAN"
    req_resources = JobRequestResources.model_validate(dict_in)
    assert req_resources.gpu_model == ["TITAN"]
    assert req_resources == TEST_JOB2_OBJ_A.request.resources.model_copy(update={"gpu_model": ["TITAN"]})


def test_resource_request_gpu_model_dict2b() -> None:
    dict_in = TEST_JOB2_OBJ_A.model_dump(mode="json", by_alias=True)
    dict_in["request"]["resources"]["gpuModel"] = "TITAN"
    job = Job.model_validate(dict_in)
    assert job.request.resources.gpu_model == ["TITAN"]
    assert job.request.resources == TEST_JOB2_OBJ_A.request.resources.model_copy(update={"gpu_model": ["TITAN"]})


def test_resource_request_gpu_model_dict2c() -> None:
    dict_in = TEST_JOB2_OBJ_A.request.model_dump(mode="json", by_alias=True)
    dict_in["resources"]["gpuModel"] = "TITAN"
    job_request = JobRequest.model_validate(dict_in)
    assert job_request.resources.gpu_model == ["TITAN"]
    assert job_request.resources == TEST_JOB2_OBJ_A.request.resources.model_copy(update={"gpu_model": ["TITAN"]})


def test_job_auto_restart_info_a() -> None:
    job1 = Job(
        id=TEST_JOB2_UUID_A,
        name="testJobA",
        deployment_environment="production",
        request=TEST_JOB2_REQUEST_OBJ_A,
        description="Test Job A",
        owner=TEST_JOB2_OWNER_OBJ_A,
        state=TEST_JOB2_STATE_OBJ_A,
        restart_info=None,
    )
    job2 = Job(
        id=TEST_JOB2_UUID_A,
        name="testJobA",
        deployment_environment="production",
        request=TEST_JOB2_REQUEST_OBJ_A,
        description="Test Job A",
        owner=TEST_JOB2_OWNER_OBJ_A,
        state=TEST_JOB2_STATE_OBJ_A,
        restart_info=RestartInfo(
            initial_job_uuid=TEST_JOB2_UUID_A,
            restart_count=0,
        ),
    )
    assert job1.restart_info
    assert job1.restart_info.initial_job_uuid == job1.id
    assert job1.restart_info.restart_count == 0

    assert job1 == job2

    actual = Job.model_validate_json(TEST_JOB2_JSON)
    assert actual == job1

    # assert "restartInfo" in job1.model_dump_json()
    # assert "restartInfo" in job1.model_dump()


def test_job2_scheduling_reservation_ids_single_a() -> None:
    dict_in = TEST_JOB2_REQUEST_SCHEDULING_OBJ_A.model_dump(mode="json", by_alias=True)
    dict_in["reservationId"] = dict_in["reservationIds"][0]  # only first element
    del dict_in["reservationIds"]
    actual = JobRequestScheduling.model_validate(dict_in)
    assert actual == TEST_JOB2_REQUEST_SCHEDULING_OBJ_A


def test_job2_scheduling_reservation_ids_single_b() -> None:
    dict_in = TEST_JOB2_REQUEST_SCHEDULING_OBJ_A.model_dump(mode="json", by_alias=True)
    dict_in["reservationId"] = dict_in["reservationIds"]  # entire list
    del dict_in["reservationIds"]
    actual = JobRequestScheduling.model_validate(dict_in)
    assert actual == TEST_JOB2_REQUEST_SCHEDULING_OBJ_A


def test_job2_scheduling_reservation_ids_single_c() -> None:
    dict_in = TEST_JOB2_REQUEST_SCHEDULING_OBJ_A.model_dump(mode="json", by_alias=True)
    dict_in["reservationId"] = "nonsense"
    del dict_in["reservationIds"]

    with pytest.raises(ValidationError):
        JobRequestScheduling.model_validate(dict_in)


def test_job2_scheduling_reservation_ids_single_d() -> None:
    dict_in = TEST_JOB2_REQUEST_SCHEDULING_OBJ_A.model_dump(mode="json", by_alias=True)
    dict_in["reservationId"] = None  # explicit None
    del dict_in["reservationIds"]

    actual = JobRequestScheduling.model_validate(dict_in)
    assert actual == TEST_JOB2_REQUEST_SCHEDULING_OBJ_A.model_copy(update={"reservation_ids": []})


def test_job2_scheduling_reservation_ids_single_e() -> None:
    dict_in = TEST_JOB2_REQUEST_SCHEDULING_OBJ_A.model_dump(mode="json", by_alias=True)
    dict_in["reservationIds"] = None  # explicit None

    actual = JobRequestScheduling.model_validate(dict_in)
    assert actual == TEST_JOB2_REQUEST_SCHEDULING_OBJ_A.model_copy(update={"reservation_ids": []})


def test_job2_scheduling_reservation_ids_single_f() -> None:
    expected = TEST_JOB2_REQUEST_SCHEDULING_OBJ_A
    dict_in = expected.model_dump(mode="json", by_alias=True)

    dict_in["reservationIds"] = None

    actual = JobRequestScheduling.model_validate(dict_in)
    assert actual == TEST_JOB2_REQUEST_SCHEDULING_OBJ_A.model_copy(update={"reservation_ids": []})


def test_job2_scheduling_reservation_ids_single_g() -> None:
    dict_in = TEST_JOB2_REQUEST_SCHEDULING_OBJ_A.model_dump(mode="json", by_alias=True)

    dict_in["reservationId"] = []
    del dict_in["reservationIds"]

    actual = JobRequestScheduling.model_validate(dict_in)
    assert actual == TEST_JOB2_REQUEST_SCHEDULING_OBJ_A.model_copy(update={"reservation_ids": []})


def test_job2_scheduling_reservation_ids_single_h() -> None:
    expected = TEST_JOB2_REQUEST_SCHEDULING_OBJ_A
    dict_in = expected.model_dump(mode="json", by_alias=True)

    dict_in["reservationIds"] = []

    actual = JobRequestScheduling.model_validate(dict_in)
    assert actual == TEST_JOB2_REQUEST_SCHEDULING_OBJ_A.model_copy(update={"reservation_ids": []})


@pytest.mark.filterwarnings("ignore::DeprecationWarning")
def test_job_sanitize() -> None:
    expected = TEST_JOB2_OBJ_A_SANITIZED
    actual = TEST_JOB2_OBJ_A.sanitized_copy(logged_in=True, same_project=False)
    assert actual == expected


@pytest.mark.filterwarnings("ignore::DeprecationWarning")
def test_job_v5_sanitize() -> None:
    actual = TEST_JOB2_OBJ_A_V5.sanitized_copy(logged_in=True, same_project=False)
    assert actual.owner is None
    # When same_project=False, sanitized_copy returns a JobV5External with owner=None
    # so we can't compare directly with a JobV5 that has an owner field
