from imecilabt.gpulab.schemas.job_filter3 import JobSort


def test_job_sort_a() -> None:
    actual = JobSort.parse_sort_string("updated")
    expected = [JobSort(column="updated", ascending=True)]
    assert actual == expected


def test_job_sort_b() -> None:
    actual = JobSort.parse_sort_string("-updated")
    expected = [JobSort(column="updated", ascending=False)]
    assert actual == expected
