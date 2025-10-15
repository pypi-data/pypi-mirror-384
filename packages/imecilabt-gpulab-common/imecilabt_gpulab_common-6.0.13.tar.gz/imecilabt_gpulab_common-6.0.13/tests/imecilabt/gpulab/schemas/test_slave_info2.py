import json
from datetime import UTC, datetime

import pytest
from imecilabt.gpulab.schemas.base import convert_datetime_to_rfc3339_string
from imecilabt.gpulab.schemas.slave_info2 import (
    STORAGE_PATH_LIMITED_CLUSTER_PROJECTS,
    GpuModel,
    ResourceInfo,
    SlaveInfo2,
    WatchdogStatistic,
)
from pydantic import ValidationError

TEST_SLAVEINFO_ACTIVE_JOB_UUID_A = "0ae7f528-ac52-4362-8d2f-ab6756977a1c"
TEST_SLAVEINFO_ACTIVE_JOB_UUID_B = "0a49e527-8e86-4803-9162-ed6509206baf"
TEST_SLAVEINFO_ACTIVE_JOB_UUID_C = "0ae7f61f-c617-46a9-bbb0-060041ab537c"


_test_time = datetime.now(tz=UTC)
_test_time_rfc3339 = convert_datetime_to_rfc3339_string(_test_time)
TEST_SLAVEINFO_A = SlaveInfo2(
    deployment_environment="production",
    name="slaveA",
    host="a.example.com",
    aliases=["A", "nickA"],
    instance_id="slaveAinst1",
    pid=45,
    cluster_id=10,
    gpu_model=[GpuModel(vendor="nvidia", name="gpumodel", memory_mb=8000)],
    cpu_model=["cpumodel1", "cpumodel2"],
    worker=ResourceInfo(system_total=10, acquired=10, used=5, available=5),
    cpu_memory_mb=ResourceInfo(system_total=1024, acquired=512, used=256, available=256),
    gpu=ResourceInfo(system_total=10, acquired=8, used=2, available=6),
    cpu=ResourceInfo(system_total=20, acquired=16, used=4, available=12),
    active_job_uuids=[
        TEST_SLAVEINFO_ACTIVE_JOB_UUID_A,
        TEST_SLAVEINFO_ACTIVE_JOB_UUID_B,
    ],
    cuda_version_full="10.1.2",
    cuda_version_major=10,
    last_update=_test_time,
    comment="a comment",
    shutting_down=True,
    docker_disk_used_percent=90.0,
    accepting_jobs=True,
    software_version="0.0.1+dev999",
)


def test_resource_info_from_json1() -> None:
    json_in = '{"systemTotal": 5, "acquired": 4, "used": 3, "available": 1}'
    actual = ResourceInfo.model_validate_json(json_in)
    assert actual.system_total == 5
    assert actual.acquired == 4
    assert actual.used == 3
    assert actual.available == 1


def test_resource_info_from_json3() -> None:
    json_in = '{"systemTotal": 5, "acquired": 4, "used": 3, "extrajunk": 2, "available": 1}'
    with pytest.raises(ValidationError, match=".*extrajunk.*"):
        ResourceInfo.model_validate_json(json_in)


def test_resource_info_from_json2a() -> None:
    json_in = '{"systemTotal": "five", "acquired": 4, "used": 3, "available": 1}'
    with pytest.raises(ValidationError, match="Input should be a valid integer"):
        ResourceInfo.model_validate_json(json_in)


def test_resource_info_from_json2b() -> None:
    json_in = '{"systemTotal": "5", "acquired": 4, "used": 3, "available": 1}'
    with pytest.raises(ValidationError, match="systemTotal"):
        ResourceInfo.model_validate_json(json_in)


def test_resource_info_from_json3a() -> None:
    json_in = '{"systemTotal": 5, "acquired": 4, "used": 3}'
    # with pytest.raises(KeyError, match='.*available.*'):
    with pytest.raises(ValidationError, match="available"):
        ResourceInfo.model_validate_json(json_in)


def test_resource_info_from_json3b() -> None:
    json_in = '{"systemTotal": 5, "acquired": 4, "used": 3, "available": 77}'
    with pytest.raises(ValidationError, match="available"):
        ResourceInfo.model_validate_json(json_in)


def test_slave_info2_to_json1() -> None:
    slave_info2_in = TEST_SLAVEINFO_A
    actual = slave_info2_in.model_dump_json(by_alias=True)
    assert "{" in actual
    assert "}" in actual
    assert "instanceId" in actual
    assert "nickA" in actual
    assert "a.example.com" in actual
    assert "systemTotal" in actual
    assert "cudaVersionFull" in actual
    assert "cudaVersionMajor" in actual
    assert "dockerDiskUsedPercent" in actual
    assert "acceptingJobs" in actual
    assert _test_time_rfc3339 in actual
    assert TEST_SLAVEINFO_ACTIVE_JOB_UUID_A in actual


@pytest.mark.filterwarnings("ignore::DeprecationWarning")
def test_slave_info2_from_json1a() -> None:
    # without cudaVersionMajor

    json_in = """{
  "deploymentEnvironment": "production",
  "name": "slaveA",
  "host": "a.example.com",
  "aliases": ["A", "nickA"],
  "instanceId": "slaveAinst1",
  "pid": 45,
  "clusterId": 10,
  "gpuModel": [
    { "vendor": "nvidia", "name": "gpumodel", "memoryMb": 8000 }
  ],
  "cpuModel": [
    "cpumodel1",
    "cpumodel2"
  ],
  "worker": {
    "systemTotal": 10,
    "acquired": 10,
    "used": 5,
    "available": 5
  },
  "cpuMemoryMb": {
    "systemTotal": 1024,
    "acquired": 512,
    "used": 256,
    "available": 256
  },
  "gpu": {
    "systemTotal": 10,
    "acquired": 8,
    "used": 2,
    "available": 6
  },
  "cpu": {
    "systemTotal": 20,
    "acquired": 16,
    "used": 4,
    "available": 12
  },
  "cudaVersionFull": "10.1.2",
  "lastUpdate": "2023-12-31T23:12:34Z",
  "comment": "a comment",
  "shuttingDown": true,
  "dockerDiskUsedPercent": 90.0,
  "acceptingJobs": true
}"""

    actual = SlaveInfo2.model_validate_json(json_in)
    assert actual.deployment_environment == "production"
    assert actual.name == "slaveA"
    assert actual.host == "a.example.com"
    assert actual.aliases == ["A", "nickA"]
    assert actual.instance_id == "slaveAinst1"
    assert actual.pid == 45
    assert actual.cluster_id == 10
    assert actual.gpu_model == [GpuModel(vendor="nvidia", name="gpumodel", memory_mb=8000)]
    assert actual.cpu_model == ["cpumodel1", "cpumodel2"]
    assert actual.worker == ResourceInfo(system_total=10, acquired=10, used=5, available=5)
    assert actual.cpu_memory_mb == ResourceInfo(system_total=1024, acquired=512, used=256, available=256)
    assert actual.gpu == ResourceInfo(system_total=10, acquired=8, used=2, available=6)
    assert actual.cpu == ResourceInfo(system_total=20, acquired=16, used=4, available=12)
    assert actual.cuda_version_full == "10.1.2"
    assert actual.cuda_version_major == 10
    assert actual.last_update == datetime(2023, 12, 31, 23, 12, 34, tzinfo=UTC)
    assert actual.comment == "a comment"
    assert actual.shutting_down is True
    assert actual.docker_disk_used_percent == 90.0
    assert actual.accepting_jobs is True


@pytest.mark.filterwarnings("ignore::DeprecationWarning")
def test_slave_info2_from_json1b() -> None:
    # with correct cudaVersionMajor

    json_in = """{
  "deploymentEnvironment": "production",
  "name": "slaveA",
  "host": "a.example.com",
  "aliases": ["A", "nickA"],
  "instanceId": "slaveAinst1",
  "pid": 45,
  "clusterId": 10,
  "gpuModel": [
    { "vendor": "nvidia", "name": "gpumodel", "memoryMb": 8000 }
  ],
  "cpuModel": [
    "cpumodel1",
    "cpumodel2"
  ],
  "worker": {
    "systemTotal": 10,
    "acquired": 10,
    "used": 5,
    "available": 5
  },
  "cpuMemoryMb": {
    "systemTotal": 1024,
    "acquired": 512,
    "used": 256,
    "available": 256
  },
  "gpu": {
    "systemTotal": 10,
    "acquired": 8,
    "used": 2,
    "available": 6
  },
  "cpu": {
    "systemTotal": 20,
    "acquired": 16,
    "used": 4,
    "available": 12
  },
  "cudaVersionMajor": 10,
  "cudaVersionFull": "10.1.2",
  "lastUpdate": "2023-12-31T23:12:34Z",
  "comment": "a comment",
  "shuttingDown": true,
  "dockerDiskUsedPercent": 95.0,
  "acceptingJobs": false
}"""

    actual = SlaveInfo2.model_validate_json(json_in)
    assert actual.deployment_environment == "production"
    assert actual.name == "slaveA"
    assert actual.host == "a.example.com"
    assert actual.aliases == ["A", "nickA"]
    assert actual.instance_id == "slaveAinst1"
    assert actual.pid == 45
    assert actual.cluster_id == 10
    assert actual.gpu_model == [GpuModel(vendor="nvidia", name="gpumodel", memory_mb=8000)]
    assert actual.cpu_model == ["cpumodel1", "cpumodel2"]
    assert actual.worker == ResourceInfo(system_total=10, acquired=10, used=5, available=5)
    assert actual.cpu_memory_mb == ResourceInfo(system_total=1024, acquired=512, used=256, available=256)
    assert actual.gpu == ResourceInfo(system_total=10, acquired=8, used=2, available=6)
    assert actual.cpu == ResourceInfo(system_total=20, acquired=16, used=4, available=12)
    assert actual.cuda_version_full == "10.1.2"
    assert actual.cuda_version_major == 10
    assert actual.last_update == datetime(2023, 12, 31, 23, 12, 34, tzinfo=UTC)
    assert actual.comment == "a comment"
    assert actual.shutting_down is True
    assert actual.docker_disk_used_percent == 95.0
    assert actual.accepting_jobs is False


def test_slave_info2_from_json1c() -> None:
    # with wrong cudaVersionMajor

    json_in = """{
  "deploymentEnvironment": "production",
  "name": "slaveA",
  "host": "a.example.com",
  "aliases": ["A", "nickA"],
  "instanceId": "slaveAinst1",
  "pid": 45,
  "clusterId": 10,
  "gpuModel": [
    { "vendor": "nvidia", "name": "gpumodel", "memoryMb": 8000 }
  ],
  "cpuModel": [
    "cpumodel1",
    "cpumodel2"
  ],
  "worker": {
    "systemTotal": 10,
    "acquired": 10,
    "used": 5,
    "available": 5
  },
  "cpuMemoryMb": {
    "systemTotal": 1024,
    "acquired": 512,
    "used": 256,
    "available": 256
  },
  "gpu": {
    "systemTotal": 10,
    "acquired": 8,
    "used": 2,
    "available": 6
  },
  "cpu": {
    "systemTotal": 20,
    "acquired": 16,
    "used": 4,
    "available": 12
  },
  "cudaVersionMajor": 11,
  "cudaVersionFull": "10.1.2",
  "lastUpdate": "2023-12-31T23:12:34Z",
  "comment": "a comment",
  "shuttingDown": true
}"""

    with pytest.raises(Exception, match=".*major.*"):
        SlaveInfo2.model_validate_json(json_in)


@pytest.mark.filterwarnings("ignore::DeprecationWarning")
def test_slave_info2_from_json1d() -> None:
    # without host and aliases

    json_in = """{
  "deploymentEnvironment": "production",
  "name": "slaveA",
  "instanceId": "slaveAinst1",
  "pid": 45,
  "clusterId": 10,
  "gpuModel": [
    { "vendor": "nvidia", "name": "gpumodel", "memoryMb": 8000 }
  ],
  "cpuModel": [
    "cpumodel1",
    "cpumodel2"
  ],
  "worker": {
    "systemTotal": 10,
    "acquired": 10,
    "used": 5,
    "available": 5
  },
  "cpuMemoryMb": {
    "systemTotal": 1024,
    "acquired": 512,
    "used": 256,
    "available": 256
  },
  "gpu": {
    "systemTotal": 10,
    "acquired": 8,
    "used": 2,
    "available": 6
  },
  "cpu": {
    "systemTotal": 20,
    "acquired": 16,
    "used": 4,
    "available": 12
  },
  "cudaVersionMajor": 10,
  "cudaVersionFull": "10.1.2",

  "lastUpdate": "2023-12-31T23:12:34Z",
  "comment": "a comment",
  "shuttingDown": true,
  "dockerDiskUsedPercent": 95.0,
  "acceptingJobs": false
}"""

    actual = SlaveInfo2.model_validate_json(json_in)
    assert actual.deployment_environment == "production"
    assert actual.name == "slaveA"
    assert actual.host is None
    assert actual.aliases == []
    assert actual.instance_id == "slaveAinst1"
    assert actual.pid == 45
    assert actual.cluster_id == 10
    assert actual.gpu_model == [GpuModel(vendor="nvidia", name="gpumodel", memory_mb=8000)]
    assert actual.cpu_model == ["cpumodel1", "cpumodel2"]
    assert actual.worker == ResourceInfo(system_total=10, acquired=10, used=5, available=5)
    assert actual.cpu_memory_mb == ResourceInfo(system_total=1024, acquired=512, used=256, available=256)
    assert actual.gpu == ResourceInfo(system_total=10, acquired=8, used=2, available=6)
    assert actual.cpu == ResourceInfo(system_total=20, acquired=16, used=4, available=12)
    assert actual.cuda_version_full == "10.1.2"
    assert actual.cuda_version_major == 10
    assert actual.last_update == datetime(2023, 12, 31, 23, 12, 34, tzinfo=UTC)
    assert actual.comment == "a comment"
    assert actual.shutting_down is True
    assert actual.docker_disk_used_percent == 95.0
    assert actual.accepting_jobs is False


def test_slave_info2_from_json1d2() -> None:
    # with wrong type in cpu model list

    json_in = """{
  "deploymentEnvironment": "production",
  "name": "slaveA",
  "host": "a.example.com",
  "aliases": ["A", "nickA"],
  "instanceId": "slaveAinst1",
  "pid": 45,
  "clusterId": 10,
  "gpuModel": [
    { "vendor": "nvidia", "name": "gpumodel", "memoryMb": 8000 }
  ],
  "cpuModel": [
    1, 2
  ],
  "worker": {
    "systemTotal": 10,
    "acquired": 10,
    "used": 5,
    "available": 5
  },
  "cpuMemoryMb": {
    "systemTotal": 1024,
    "acquired": 512,
    "used": 256,
    "available": 256
  },
  "gpu": {
    "systemTotal": 10,
    "acquired": 8,
    "used": 2,
    "available": 6
  },
  "cpu": {
    "systemTotal": 20,
    "acquired": 16,
    "used": 4,
    "available": 12
  },
  "cudaVersionMajor": 10,
  "cudaVersionFull": "10.1.2",

  "lastUpdate": "2023-12-31T23:12:34Z",
  "comment": "a comment",
  "shuttingDown": true
}"""

    with pytest.raises(Exception, match=".*cpu_?[mM]odel.*"):
        SlaveInfo2.model_validate_json(json_in)


def test_watchdog_statistics_to_json() -> None:
    test_time = datetime(2021, 2, 3, 4, 5, 6, tzinfo=UTC)
    test_time_rfc3339 = convert_datetime_to_rfc3339_string(test_time)

    obj_in = WatchdogStatistic(
        alive_now=True,
        last_alive_date=test_time,
        alarm_counts={"tst": 5},
        alarm_last_dates={"tst": test_time_rfc3339},  # type: ignore[dict-item]
        emails_sent=10,
    )

    dict_out = json.loads(obj_in.model_dump_json(by_alias=True))
    assert dict_out["aliveNow"] is True
    assert "lastAliveDate" in dict_out
    assert isinstance(dict_out["lastAliveDate"], str), "did not convert datetime to str: {}".format(
        type(dict_out["lastAliveDate"]).__name__
    )
    assert dict_out["lastAliveDate"] == test_time_rfc3339
    assert "alarmLastDates" in dict_out
    assert "tst" in dict_out["alarmLastDates"]
    assert isinstance(dict_out["alarmLastDates"]["tst"], str), "did not convert datetime to str: {}".format(
        type(dict_out["alarmLastDates"]["tst"]).__name__
    )
    assert dict_out["alarmLastDates"]["tst"] == test_time_rfc3339

    json_out = obj_in.model_dump_json(by_alias=True)
    assert test_time_rfc3339 in json_out
    dict_out_in = json.loads(json_out)
    assert dict_out_in["aliveNow"] is True
    assert "lastAliveDate" in dict_out_in
    assert isinstance(dict_out_in["lastAliveDate"], str), "did not convert datetime to str: {}".format(
        type(dict_out_in["lastAliveDate"]).__name__
    )
    assert dict_out_in["lastAliveDate"] == test_time_rfc3339
    assert "alarmLastDates" in dict_out_in
    assert "tst" in dict_out_in["alarmLastDates"]
    assert isinstance(dict_out_in["alarmLastDates"]["tst"], str), "did not convert datetime to str: {}".format(
        type(dict_out_in["alarmLastDates"]["tst"]).__name__
    )
    assert dict_out_in["alarmLastDates"]["tst"] == test_time_rfc3339

    actual = WatchdogStatistic.model_validate_json(json_out)
    assert isinstance(actual, WatchdogStatistic)
    assert actual.alive_now is True
    assert actual.emails_sent == 10
    assert actual.alarm_counts == {"tst": 5}
    assert actual.last_alive_date == test_time
    assert actual.alarm_last_dates == {"tst": test_time}

    copy = obj_in.model_copy()
    assert isinstance(copy, WatchdogStatistic)
    assert copy.alive_now is True
    assert copy.emails_sent == 10
    assert copy.alarm_counts == {"tst": 5}
    assert copy.last_alive_date == test_time
    assert copy.alarm_last_dates == {"tst": test_time}


def test_name_matches() -> None:
    slave_info2 = SlaveInfo2(
        deployment_environment="production",
        name="slaveA1",
        host="a.example.com",
        aliases=["A1", "nick A1"],
        instance_id="slaveA1inst1",
        pid=45,
        cluster_id=10,
        gpu_model=[GpuModel(vendor="nvidia", name="gpumodel", memory_mb=8000)],
        cpu_model=["cpumodel1", "cpumodel2"],
        worker=ResourceInfo(system_total=10, acquired=10, used=5, available=5),
        cpu_memory_mb=ResourceInfo(system_total=1024, acquired=512, used=256, available=256),
        gpu=ResourceInfo(system_total=10, acquired=8, used=2, available=6),
        cpu=ResourceInfo(system_total=20, acquired=16, used=4, available=12),
        active_job_uuids=[TEST_SLAVEINFO_ACTIVE_JOB_UUID_A],
        cuda_version_full="10.1.2",
        cuda_version_major=10,
        last_update=datetime.now(UTC),
        comment="a comment",
        shutting_down=True,
        docker_disk_used_percent=90.0,
        accepting_jobs=True,
        software_version="0.0.1+dev999",
    )

    assert slave_info2.matches_name("A1")
    assert slave_info2.matches_name("a1")
    assert slave_info2.matches_name("A 1")
    assert slave_info2.matches_name("_A_1_")
    assert slave_info2.matches_name("nick A1")
    assert slave_info2.matches_name("NICKA1")
    assert slave_info2.matches_name("nick_A1")
    assert slave_info2.matches_name("slaveA1")
    assert slave_info2.matches_name("SLAVEa1")
    assert slave_info2.matches_name("SLAVE A1")
    assert slave_info2.matches_name(" S__L A V$$$$E  &^  A 1   *")

    assert not slave_info2.matches_name("SLAVEA")
    assert not slave_info2.matches_name("a")
    assert not slave_info2.matches_name("a2")
    assert not slave_info2.matches_name("nick A")
    assert not slave_info2.matches_name("A1nick")
    assert not slave_info2.matches_name("slave")
    assert not slave_info2.matches_name("nick")


_TEST_PROJ_URN1a = "urn:publicid:IDN+example.com+project+project1"
_TEST_PROJ_URN1b = "urn:publicid:IDN+example.com+project+Project1"
_TEST_PROJ_URN2a = "urn:publicid:IDN+example.com+project+Project2"
_TEST_PROJ_URN2b = "urn:publicid:IDN+example.com+project+PROJECT2"
_TEST_PROJ_URN3 = "urn:publicid:IDN+example.com+project+p3"


def test_has_storage_1() -> None:
    slave_info2 = TEST_SLAVEINFO_A.model_copy(
        update={
            "storage_paths_available": ["/project", "/project_scratch/"],
            "storage_aliases_available": {
                "/project_alias1": "/project",
                "/project_alias2/": "/project",
                "/project_alias3/": "/project/",
                "/project_alias4": "/project/",
                "/project_scratch_alias1": "/project_scratch",
                "/project_scratch_alias2/": "/project_scratch",
                "/project_scratch_alias3/": "/project_scratch/",
                "/project_scratch_alias4": "/project_scratch/",
            },
            "storage_paths_available_project_limited": {
                "/project/": [_TEST_PROJ_URN1a, _TEST_PROJ_URN2a],
                "/project_scratch/": [_TEST_PROJ_URN1b, _TEST_PROJ_URN2b],
            },
        }
    )

    assert slave_info2.has_storage("/project")
    assert slave_info2.has_storage("/project/")
    assert slave_info2.has_storage("/project/foo/")
    assert slave_info2.has_storage("/project/foo/bar")
    assert not slave_info2.has_storage("project")
    assert not slave_info2.has_storage("/PROJECT")

    assert not slave_info2.has_storage("/project_alias")
    assert not slave_info2.has_storage("/project_alias/")

    assert slave_info2.has_storage("/project_alias1")
    assert slave_info2.has_storage("/project_alias1/")
    assert slave_info2.has_storage("/project_alias1/foo/")
    assert slave_info2.has_storage("/project_alias1/foo/bar")

    assert slave_info2.has_storage("/project_alias2")
    assert slave_info2.has_storage("/project_alias2/")
    assert slave_info2.has_storage("/project_alias2/foo/")
    assert slave_info2.has_storage("/project_alias2/foo/bar")

    assert slave_info2.has_storage("/project_alias3")
    assert slave_info2.has_storage("/project_alias3/")
    assert slave_info2.has_storage("/project_alias3/foo/")
    assert slave_info2.has_storage("/project_alias3/foo/bar")

    assert slave_info2.has_storage("/project_alias4")
    assert slave_info2.has_storage("/project_alias4/")
    assert slave_info2.has_storage("/project_alias4/foo/")
    assert slave_info2.has_storage("/project_alias4/foo/bar")


def test_allows_storage_1() -> None:
    slave_info2 = TEST_SLAVEINFO_A.model_copy(
        update={
            "storage_paths_available": ["/project", "/project_scratch/"],
            "storage_aliases_available": {
                "/project_alias1": "/project",
                "/project_alias2/": "/project",
                "/project_alias3/": "/project/",
                "/project_alias4": "/project/",
                "/project_scratch_alias1": "/project_scratch",
                "/project_scratch_alias2/": "/project_scratch",
                "/project_scratch_alias3/": "/project_scratch/",
                "/project_scratch_alias4": "/project_scratch/",
            },
            "storage_paths_available_project_limited": {
                "/project/": [_TEST_PROJ_URN1a, _TEST_PROJ_URN2a],
                "/project_scratch/": [_TEST_PROJ_URN1b, _TEST_PROJ_URN2b],
            },
        }
    )

    for proj_urn in (
        _TEST_PROJ_URN1a,
        _TEST_PROJ_URN1b,
        _TEST_PROJ_URN2a,
        _TEST_PROJ_URN2b,
    ):
        assert slave_info2.allows_storage("/project", proj_urn), f"Failed allow_storage for proj_urn={proj_urn}"
        assert slave_info2.allows_storage("/project/", proj_urn)
        assert slave_info2.allows_storage("/project/foo/", proj_urn)
        assert slave_info2.allows_storage("/project/foo/bar", proj_urn)
        assert not slave_info2.allows_storage("project", proj_urn)
        assert not slave_info2.allows_storage("/PROJECT", proj_urn)

        assert not slave_info2.allows_storage("/project_alias", proj_urn)
        assert not slave_info2.allows_storage("/project_alias/", proj_urn)

        assert slave_info2.allows_storage("/project_alias1", proj_urn)
        assert slave_info2.allows_storage("/project_alias1/", proj_urn)
        assert slave_info2.allows_storage("/project_alias1/foo/", proj_urn)
        assert slave_info2.allows_storage("/project_alias1/foo/bar", proj_urn)

        assert slave_info2.allows_storage("/project_alias2", proj_urn)
        assert slave_info2.allows_storage("/project_alias2/", proj_urn)
        assert slave_info2.allows_storage("/project_alias2/foo/", proj_urn)
        assert slave_info2.allows_storage("/project_alias2/foo/bar", proj_urn)

        assert slave_info2.allows_storage("/project_alias3", proj_urn)
        assert slave_info2.allows_storage("/project_alias3/", proj_urn)
        assert slave_info2.allows_storage("/project_alias3/foo/", proj_urn)
        assert slave_info2.allows_storage("/project_alias3/foo/bar", proj_urn)

        assert slave_info2.allows_storage("/project_alias4", proj_urn)
        assert slave_info2.allows_storage("/project_alias4/", proj_urn)
        assert slave_info2.allows_storage("/project_alias4/foo/", proj_urn)
        assert slave_info2.allows_storage("/project_alias4/foo/bar", proj_urn)

    proj_urn = _TEST_PROJ_URN3
    assert not slave_info2.allows_storage("/project", proj_urn)
    assert not slave_info2.allows_storage("/project/", proj_urn)
    assert not slave_info2.allows_storage("/project/foo/", proj_urn)
    assert not slave_info2.allows_storage("/project/foo/bar", proj_urn)
    assert not slave_info2.allows_storage("project", proj_urn)
    assert not slave_info2.allows_storage("/PROJECT", proj_urn)

    assert not slave_info2.allows_storage("/project_alias", proj_urn)
    assert not slave_info2.allows_storage("/project_alias/", proj_urn)

    assert not slave_info2.allows_storage("/project_alias1", proj_urn)
    assert not slave_info2.allows_storage("/project_alias1/", proj_urn)
    assert not slave_info2.allows_storage("/project_alias1/foo/", proj_urn)
    assert not slave_info2.allows_storage("/project_alias1/foo/bar", proj_urn)

    assert not slave_info2.allows_storage("/project_alias2", proj_urn)
    assert not slave_info2.allows_storage("/project_alias2/", proj_urn)
    assert not slave_info2.allows_storage("/project_alias2/foo/", proj_urn)
    assert not slave_info2.allows_storage("/project_alias2/foo/bar", proj_urn)

    assert not slave_info2.allows_storage("/project_alias3", proj_urn)
    assert not slave_info2.allows_storage("/project_alias3/", proj_urn)
    assert not slave_info2.allows_storage("/project_alias3/foo/", proj_urn)
    assert not slave_info2.allows_storage("/project_alias3/foo/bar", proj_urn)

    assert not slave_info2.allows_storage("/project_alias4", proj_urn)
    assert not slave_info2.allows_storage("/project_alias4/", proj_urn)
    assert not slave_info2.allows_storage("/project_alias4/foo/", proj_urn)
    assert not slave_info2.allows_storage("/project_alias4/foo/bar", proj_urn)


def test_allows_storage_2() -> None:
    slave_info2 = TEST_SLAVEINFO_A.model_copy(
        update={
            "storage_paths_available": ["/project", "/project_scratch/"],
            "storage_aliases_available": {
                "/project_alias1": "/project",
                "/project_alias2/": "/project",
                "/project_alias3/": "/project/",
                "/project_alias4": "/project/",
                "/project_scratch_alias1": "/project_scratch",
                "/project_scratch_alias2/": "/project_scratch",
                "/project_scratch_alias3/": "/project_scratch/",
                "/project_scratch_alias4": "/project_scratch/",
            },
            "storage_paths_available_project_limited": {"/project/": []},
        }
    )

    for proj_urn in (
        _TEST_PROJ_URN1a,
        _TEST_PROJ_URN1b,
        _TEST_PROJ_URN2a,
        _TEST_PROJ_URN2b,
        _TEST_PROJ_URN3,
    ):
        assert not slave_info2.allows_storage("/project", proj_urn), f"Failed allow_storage for proj_urn={proj_urn}"
        assert not slave_info2.allows_storage("/project/", proj_urn)
        assert not slave_info2.allows_storage("/project/foo/", proj_urn)
        assert not slave_info2.allows_storage("/project/foo/bar", proj_urn)

        assert slave_info2.allows_storage("/project_scratch", proj_urn)
        assert slave_info2.allows_storage("/project_scratch/", proj_urn)
        assert slave_info2.allows_storage("/project_scratch/foo/", proj_urn)
        assert slave_info2.allows_storage("/project_scratch/foo/bar", proj_urn)

        assert not slave_info2.allows_storage("project", proj_urn)
        assert not slave_info2.allows_storage("/PROJECT", proj_urn)

        assert not slave_info2.allows_storage("/project_alias", proj_urn)
        assert not slave_info2.allows_storage("/project_alias/", proj_urn)

        assert not slave_info2.allows_storage("/project_alias1", proj_urn)
        assert not slave_info2.allows_storage("/project_alias1/", proj_urn)
        assert not slave_info2.allows_storage("/project_alias1/foo/", proj_urn)
        assert not slave_info2.allows_storage("/project_alias1/foo/bar", proj_urn)

        assert not slave_info2.allows_storage("/project_alias2", proj_urn)
        assert not slave_info2.allows_storage("/project_alias2/", proj_urn)
        assert not slave_info2.allows_storage("/project_alias2/foo/", proj_urn)
        assert not slave_info2.allows_storage("/project_alias2/foo/bar", proj_urn)

        assert not slave_info2.allows_storage("/project_alias3", proj_urn)
        assert not slave_info2.allows_storage("/project_alias3/", proj_urn)
        assert not slave_info2.allows_storage("/project_alias3/foo/", proj_urn)
        assert not slave_info2.allows_storage("/project_alias3/foo/bar", proj_urn)

        assert not slave_info2.allows_storage("/project_alias4", proj_urn)
        assert not slave_info2.allows_storage("/project_alias4/", proj_urn)
        assert not slave_info2.allows_storage("/project_alias4/foo/", proj_urn)
        assert not slave_info2.allows_storage("/project_alias4/foo/bar", proj_urn)

        assert not slave_info2.allows_storage("/project_scratch_alias", proj_urn)
        assert not slave_info2.allows_storage("/project_scratch_alias/", proj_urn)

        assert slave_info2.allows_storage("/project_scratch_alias1", proj_urn)
        assert slave_info2.allows_storage("/project_scratch_alias1/", proj_urn)
        assert slave_info2.allows_storage("/project_scratch_alias1/foo/", proj_urn)
        assert slave_info2.allows_storage("/project_scratch_alias1/foo/bar", proj_urn)

        assert slave_info2.allows_storage("/project_scratch_alias2", proj_urn)
        assert slave_info2.allows_storage("/project_scratch_alias2/", proj_urn)
        assert slave_info2.allows_storage("/project_scratch_alias2/foo/", proj_urn)
        assert slave_info2.allows_storage("/project_scratch_alias2/foo/bar", proj_urn)

        assert slave_info2.allows_storage("/project_scratch_alias3", proj_urn)
        assert slave_info2.allows_storage("/project_scratch_alias3/", proj_urn)
        assert slave_info2.allows_storage("/project_scratch_alias3/foo/", proj_urn)
        assert slave_info2.allows_storage("/project_scratch_alias3/foo/bar", proj_urn)

        assert slave_info2.allows_storage("/project_scratch_alias4", proj_urn)
        assert slave_info2.allows_storage("/project_scratch_alias4/", proj_urn)
        assert slave_info2.allows_storage("/project_scratch_alias4/foo/", proj_urn)
        assert slave_info2.allows_storage("/project_scratch_alias4/foo/bar", proj_urn)


def test_allows_storage_3() -> None:
    slave_info2 = TEST_SLAVEINFO_A.model_copy(
        update={
            "storage_paths_available": ["/project", "/project_scratch/"],
            "storage_aliases_available": {
                "/project_alias1": "/project",
                "/project_alias2/": "/project",
                "/project_alias3/": "/project/",
                "/project_alias4": "/project/",
                "/project_scratch_alias1": "/project_scratch",
                "/project_scratch_alias2/": "/project_scratch",
                "/project_scratch_alias3/": "/project_scratch/",
                "/project_scratch_alias4": "/project_scratch/",
            },
            "storage_paths_available_project_limited": {
                "/project/": [STORAGE_PATH_LIMITED_CLUSTER_PROJECTS],
                "/project_scratch/": [_TEST_PROJ_URN1b, _TEST_PROJ_URN2b],
            },
        }
    )

    cluster_projects_allowed = [_TEST_PROJ_URN1a, _TEST_PROJ_URN2a]

    for proj_urn in (
        _TEST_PROJ_URN1a,
        _TEST_PROJ_URN1b,
        _TEST_PROJ_URN2a,
        _TEST_PROJ_URN2b,
    ):
        assert slave_info2.allows_storage("/project", proj_urn, cluster_projects_allowed=cluster_projects_allowed)
        assert slave_info2.allows_storage("/project/", proj_urn, cluster_projects_allowed=cluster_projects_allowed)
        assert slave_info2.allows_storage("/project/foo/", proj_urn, cluster_projects_allowed=cluster_projects_allowed)
        assert slave_info2.allows_storage(
            "/project/foo/bar",
            proj_urn,
            cluster_projects_allowed=cluster_projects_allowed,
        )
        assert not slave_info2.allows_storage("project", proj_urn, cluster_projects_allowed=cluster_projects_allowed)
        assert not slave_info2.allows_storage("/PROJECT", proj_urn, cluster_projects_allowed=cluster_projects_allowed)

        assert not slave_info2.allows_storage(
            "/project_alias",
            proj_urn,
            cluster_projects_allowed=cluster_projects_allowed,
        )
        assert not slave_info2.allows_storage(
            "/project_alias/",
            proj_urn,
            cluster_projects_allowed=cluster_projects_allowed,
        )

        assert slave_info2.allows_storage(
            "/project_alias1",
            proj_urn,
            cluster_projects_allowed=cluster_projects_allowed,
        )
        assert slave_info2.allows_storage(
            "/project_alias1/",
            proj_urn,
            cluster_projects_allowed=cluster_projects_allowed,
        )
        assert slave_info2.allows_storage(
            "/project_alias1/foo/",
            proj_urn,
            cluster_projects_allowed=cluster_projects_allowed,
        )
        assert slave_info2.allows_storage(
            "/project_alias1/foo/bar",
            proj_urn,
            cluster_projects_allowed=cluster_projects_allowed,
        )

        assert slave_info2.allows_storage(
            "/project_alias2",
            proj_urn,
            cluster_projects_allowed=cluster_projects_allowed,
        )
        assert slave_info2.allows_storage(
            "/project_alias2/",
            proj_urn,
            cluster_projects_allowed=cluster_projects_allowed,
        )
        assert slave_info2.allows_storage(
            "/project_alias2/foo/",
            proj_urn,
            cluster_projects_allowed=cluster_projects_allowed,
        )
        assert slave_info2.allows_storage(
            "/project_alias2/foo/bar",
            proj_urn,
            cluster_projects_allowed=cluster_projects_allowed,
        )

        assert slave_info2.allows_storage(
            "/project_alias3",
            proj_urn,
            cluster_projects_allowed=cluster_projects_allowed,
        )
        assert slave_info2.allows_storage(
            "/project_alias3/",
            proj_urn,
            cluster_projects_allowed=cluster_projects_allowed,
        )
        assert slave_info2.allows_storage(
            "/project_alias3/foo/",
            proj_urn,
            cluster_projects_allowed=cluster_projects_allowed,
        )
        assert slave_info2.allows_storage(
            "/project_alias3/foo/bar",
            proj_urn,
            cluster_projects_allowed=cluster_projects_allowed,
        )

        assert slave_info2.allows_storage(
            "/project_alias4",
            proj_urn,
            cluster_projects_allowed=cluster_projects_allowed,
        )
        assert slave_info2.allows_storage(
            "/project_alias4/",
            proj_urn,
            cluster_projects_allowed=cluster_projects_allowed,
        )
        assert slave_info2.allows_storage(
            "/project_alias4/foo/",
            proj_urn,
            cluster_projects_allowed=cluster_projects_allowed,
        )
        assert slave_info2.allows_storage(
            "/project_alias4/foo/bar",
            proj_urn,
            cluster_projects_allowed=cluster_projects_allowed,
        )

    proj_urn = _TEST_PROJ_URN3
    assert not slave_info2.allows_storage("/project", proj_urn, cluster_projects_allowed=cluster_projects_allowed)
    assert not slave_info2.allows_storage("/project/", proj_urn, cluster_projects_allowed=cluster_projects_allowed)
    assert not slave_info2.allows_storage("/project/foo/", proj_urn, cluster_projects_allowed=cluster_projects_allowed)
    assert not slave_info2.allows_storage(
        "/project/foo/bar", proj_urn, cluster_projects_allowed=cluster_projects_allowed
    )
    assert not slave_info2.allows_storage("project", proj_urn, cluster_projects_allowed=cluster_projects_allowed)
    assert not slave_info2.allows_storage("/PROJECT", proj_urn, cluster_projects_allowed=cluster_projects_allowed)

    assert not slave_info2.allows_storage("/project_alias", proj_urn, cluster_projects_allowed=cluster_projects_allowed)
    assert not slave_info2.allows_storage(
        "/project_alias/", proj_urn, cluster_projects_allowed=cluster_projects_allowed
    )

    assert not slave_info2.allows_storage(
        "/project_alias1", proj_urn, cluster_projects_allowed=cluster_projects_allowed
    )
    assert not slave_info2.allows_storage(
        "/project_alias1/", proj_urn, cluster_projects_allowed=cluster_projects_allowed
    )
    assert not slave_info2.allows_storage(
        "/project_alias1/foo/",
        proj_urn,
        cluster_projects_allowed=cluster_projects_allowed,
    )
    assert not slave_info2.allows_storage(
        "/project_alias1/foo/bar",
        proj_urn,
        cluster_projects_allowed=cluster_projects_allowed,
    )

    assert not slave_info2.allows_storage(
        "/project_alias2", proj_urn, cluster_projects_allowed=cluster_projects_allowed
    )
    assert not slave_info2.allows_storage(
        "/project_alias2/", proj_urn, cluster_projects_allowed=cluster_projects_allowed
    )
    assert not slave_info2.allows_storage(
        "/project_alias2/foo/",
        proj_urn,
        cluster_projects_allowed=cluster_projects_allowed,
    )
    assert not slave_info2.allows_storage(
        "/project_alias2/foo/bar",
        proj_urn,
        cluster_projects_allowed=cluster_projects_allowed,
    )

    assert not slave_info2.allows_storage(
        "/project_alias3", proj_urn, cluster_projects_allowed=cluster_projects_allowed
    )
    assert not slave_info2.allows_storage(
        "/project_alias3/", proj_urn, cluster_projects_allowed=cluster_projects_allowed
    )
    assert not slave_info2.allows_storage(
        "/project_alias3/foo/",
        proj_urn,
        cluster_projects_allowed=cluster_projects_allowed,
    )
    assert not slave_info2.allows_storage(
        "/project_alias3/foo/bar",
        proj_urn,
        cluster_projects_allowed=cluster_projects_allowed,
    )

    assert not slave_info2.allows_storage(
        "/project_alias4", proj_urn, cluster_projects_allowed=cluster_projects_allowed
    )
    assert not slave_info2.allows_storage(
        "/project_alias4/", proj_urn, cluster_projects_allowed=cluster_projects_allowed
    )
    assert not slave_info2.allows_storage(
        "/project_alias4/foo/",
        proj_urn,
        cluster_projects_allowed=cluster_projects_allowed,
    )
    assert not slave_info2.allows_storage(
        "/project_alias4/foo/bar",
        proj_urn,
        cluster_projects_allowed=cluster_projects_allowed,
    )
