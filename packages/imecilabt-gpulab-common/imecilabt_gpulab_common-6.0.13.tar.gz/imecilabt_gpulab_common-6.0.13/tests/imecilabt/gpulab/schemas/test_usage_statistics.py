from datetime import datetime

import jsondiff
from imecilabt.gpulab.schemas.usage_statistics import (
    ContainerUsageStatistics,
    GpuInfo,
    GPULabUsageStatistics,
    GpuOverview,
    GpuUsageStatistics,
)

TEST_CPU_USAGE_STATISTICS_JSON = """{
    "firstTime": "2020-03-01T07:00:01Z",
    "lastTime": "2020-03-01T07:00:03Z",
    "aggPeriodNs": 2000000000,
    "cpuCount": 2,
    "cpuUsage": 1.3,
    "cpuUsageTotalNs": 1300000000,
    "cpuUsageKernelmodeNs": 200000000,
    "cpuUsageUsermodeNs": 1100000000,
    "maxPidCount": 5,
    "memLimitByte": 5000000000,
    "memUsageByte": 254000000,
    "memMaxUsageByte": 254000000,
    "networkRxByte": 5000,
    "networkTxByte": 60000
}"""

TEST_CPU_USAGE_STATISTICS_OBJ = ContainerUsageStatistics(
    first_time=datetime.fromisoformat("2020-03-01T07:00:01Z"),
    last_time=datetime.fromisoformat("2020-03-01T07:00:03Z"),
    agg_period_ns=2000000000,
    cpu_count=2,
    cpu_usage=1.3,
    cpu_usage_total_ns=1300000000,
    cpu_usage_kernelmode_ns=200000000,
    cpu_usage_usermode_ns=1100000000,
    max_pid_count=5,
    mem_limit_byte=5000000000,
    mem_usage_byte=254000000,
    mem_max_usage_byte=254000000,
    network_rx_byte=5000,
    network_tx_byte=60000,
)


def test_cpu_usage_statistics() -> None:
    actual = ContainerUsageStatistics.model_validate_json(TEST_CPU_USAGE_STATISTICS_JSON)
    assert actual == TEST_CPU_USAGE_STATISTICS_OBJ
    assert not jsondiff.diff(
        TEST_CPU_USAGE_STATISTICS_JSON,
        actual.model_dump_json(by_alias=True, exclude_none=True),
        load=True,
    )


TEST_GPU_USAGE_STATISTICS_JSON = """{
    "gpuCount": 3,
    "averageUtilization": 23.0,
    "averageMemUtilization": 99.0
}"""

TEST_GPU_USAGE_STATISTICS_OBJ = GpuUsageStatistics(
    gpu_count=3,
    average_utilization=23.0,
    average_mem_utilization=99.0,
)


def test_gpu_usage_statistics() -> None:
    actual = GpuUsageStatistics.model_validate_json(TEST_GPU_USAGE_STATISTICS_JSON)
    assert actual == TEST_GPU_USAGE_STATISTICS_OBJ
    assert not jsondiff.diff(
        TEST_GPU_USAGE_STATISTICS_JSON,
        actual.model_dump_json(by_alias=True, exclude_none=True),
        load=True,
    )


TEST_GPULAB_USAGE_STATISTICS_JSON = (
    """{
"containerStatistics": """
    + TEST_CPU_USAGE_STATISTICS_JSON
    + """,
"gpuStatistics": """
    + TEST_GPU_USAGE_STATISTICS_JSON
    + """
}"""
)

TEST_GPULAB_USAGE_STATISTICS_OBJ = GPULabUsageStatistics(
    container_statistics=TEST_CPU_USAGE_STATISTICS_OBJ,
    gpu_statistics=TEST_GPU_USAGE_STATISTICS_OBJ,
)


def test_gpulab_usage_statistics() -> None:
    actual = GPULabUsageStatistics.model_validate_json(TEST_GPULAB_USAGE_STATISTICS_JSON)
    assert actual == TEST_GPULAB_USAGE_STATISTICS_OBJ
    assert not jsondiff.diff(
        TEST_GPULAB_USAGE_STATISTICS_JSON,
        actual.model_dump_json(by_alias=True, exclude_none=True),
        load=True,
    )


TEST_GPU_INFO_JSON = """{
 "boardId": 768,
 "brand": "GeForce",
 "bridgeChipInfo": "N/A",
 "index": 0,
 "isMultiGpuBoard": false,
 "maxPcieLinkGeneration": 3,
 "maxPcieLinkWidth": 16,
 "minorNumber": 0,
 "name": "GeForce GTX 980",
 "serial": "N/A",
 "uuid": "GPU-8a56a4bc-e184-a047-2620-be19fdf913d5",
 "vbiosVersion": "84.04.31.00.29"
}"""

TEST_GPU_INFO_OBJ = GpuInfo(
    board_id=768,
    brand="GeForce",
    bridge_chip_info="N/A",
    index=0,
    is_multi_gpu_board=False,
    max_pcie_link_generation=3,
    max_pcie_link_width=16,
    minor_number=0,
    name="GeForce GTX 980",
    serial="N/A",
    uuid="GPU-8a56a4bc-e184-a047-2620-be19fdf913d5",
    vbios_version="84.04.31.00.29",
)


def test_gpu_info() -> None:
    actual = GpuInfo.model_validate_json(TEST_GPU_INFO_JSON)
    assert actual == TEST_GPU_INFO_OBJ
    assert not jsondiff.diff(
        TEST_GPU_INFO_JSON,
        actual.model_dump_json(by_alias=True, exclude_none=True),
        load=True,
    )


TEST_GPU_OVERVIEW_JSON = (
    """{
 "cudaVersionFull": "10.2.0",
 "cudaVersionInt": 10020,
 "cudaVersionMajor": 10,
 "cudaVersionMinor": 2.0,
 "driverVersion": "440.33.01",
 "nvmlVersion": "10.440.33.01",
 "gpus": [ """
    + TEST_GPU_INFO_JSON
    + """]
}"""
)


TEST_GPU_OVERVIEW_OBJ = GpuOverview(
    cuda_version_full="10.2.0",
    cuda_version_int=10020,
    cuda_version_major=10,
    cuda_version_minor=2.0,
    driver_version="440.33.01",
    nvml_version="10.440.33.01",
    gpus=[TEST_GPU_INFO_OBJ],
)


def test_gpu_overview() -> None:
    actual = GpuOverview.model_validate_json(TEST_GPU_OVERVIEW_JSON)
    assert actual == TEST_GPU_OVERVIEW_OBJ
    assert not jsondiff.diff(
        TEST_GPU_OVERVIEW_JSON,
        actual.model_dump_json(by_alias=True, exclude_none=True),
        load=True,
    )
