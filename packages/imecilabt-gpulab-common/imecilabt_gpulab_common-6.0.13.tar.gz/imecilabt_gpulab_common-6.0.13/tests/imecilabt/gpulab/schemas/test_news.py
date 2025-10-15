from datetime import UTC, datetime

import jsondiff
import pytest
from imecilabt.gpulab.schemas.news import News
from pydantic import ValidationError


def test_news_from_json1() -> None:
    json_in = """{
    "id": "9a6355d0-6d06-11ea-a8da-7b5b9b861935",
    "created": "2020-03-23T06:38:34Z",
    "enabled": true,
    "type": "WARNING",
    "title": "Planned Maintenance Friday Morning",
    "text": "TestText",
    "notBefore": "2020-03-24T00:00:00Z",
    "notAfter": "2020-03-30T12:00:00Z",
    "tags": [ "MAINTENANCE", "WEBSITE", "CLI" ]
 }"""

    actual = News.model_validate_json(json_in)
    assert actual.id == "9a6355d0-6d06-11ea-a8da-7b5b9b861935"
    assert actual.created == datetime.fromisoformat("2020-03-23T06:38:34Z")
    assert actual.enabled is True
    assert actual.type == "WARNING"
    assert actual.title == "Planned Maintenance Friday Morning"
    assert actual.text == "TestText"
    assert actual.not_before == datetime.fromisoformat("2020-03-24T00:00:00Z")
    assert actual.not_after == datetime.fromisoformat("2020-03-30T12:00:00Z")
    assert actual.tags == ["MAINTENANCE", "WEBSITE", "CLI"]

    # Serialize again and compare against input
    assert not jsondiff.diff(json_in, actual.model_dump_json(by_alias=True), load=True)


def test_news_from_json2() -> None:
    json_in = """{
    "id": "9a6355d0-6d06-11ea-a8da-7b5b9b861935",
    "created": "2020-03-23T06:38:34Z",
    "enabled": false,
    "type": "WARNING",
    "title": "Planned Maintenance Friday Morning",
    "text": "TestText",
    "notBefore": null,
    "notAfter": null,
    "tags": [ "MAINTENANCE" ]
 }"""
    actual = News.model_validate_json(json_in)
    assert actual.id == "9a6355d0-6d06-11ea-a8da-7b5b9b861935"
    assert actual.created == datetime.fromisoformat("2020-03-23T06:38:34Z")
    assert actual.enabled is False
    assert actual.type == "WARNING"
    assert actual.title == "Planned Maintenance Friday Morning"
    assert actual.text == "TestText"
    assert actual.not_before is None
    assert actual.not_after is None
    assert actual.tags == ["MAINTENANCE"]

    # Serialize again and compare against input
    assert not jsondiff.diff(json_in, actual.model_dump_json(by_alias=True), load=True)


def test_news_from_json3() -> None:
    # notBefore and notAfter is missing here
    json_in = """{
    "id": "9a6355d0-6d06-11ea-a8da-7b5b9b861935",
    "created": "2020-03-23T06:38:34Z",
    "enabled": true,
    "type": "WARNING",
    "title": "Planned Maintenance Friday Morning",
    "text": "TestText",
    "tags": [  ]
 }"""
    actual = News.model_validate_json(json_in)
    assert actual.id == "9a6355d0-6d06-11ea-a8da-7b5b9b861935"
    assert actual.created == datetime.fromisoformat("2020-03-23T06:38:34Z")
    assert actual.enabled is True
    assert actual.type == "WARNING"
    assert actual.title == "Planned Maintenance Friday Morning"
    assert actual.text == "TestText"
    assert actual.not_before is None
    assert actual.not_after is None
    assert actual.tags == []

    # Serialize again and compare against input
    assert jsondiff.diff(json_in, actual.model_dump_json(by_alias=True), load=True).keys() == {"notBefore", "notAfter"}


def test_invalid_notafter() -> None:
    # notBefore comes after notAfter here
    json_in = """{
    "id": "9a6355d0-6d06-11ea-a8da-7b5b9b861935",
    "created": "2020-03-23T06:38:34Z",
    "enabled": true,
    "type": "WARNING",
    "title": "Planned Maintenance Friday Morning",
    "text": "TestText",
    "tags": [  ],
    "notBefore": "2020-04-24T00:00:00Z",
    "notAfter": "2020-03-30T12:00:00Z"
 }"""
    with pytest.raises(ValidationError, match="notAfter must come after notBefore"):
        News.model_validate_json(json_in)


def test_news_to_json1() -> None:
    news_in = News(
        id="9a6355d0-6d06-11ea-a8da-7b5b9b861935",
        created=datetime.fromisoformat("2020-03-23T06:38:34Z"),
        enabled=True,
        type="WARNING",
        title="Planned Maintenance Friday Morning",
        text="TestText",
        tags=["MAINTENANCE", "WEBSITE", "CLI"],
        not_before=datetime.fromisoformat("2020-03-24T00:00:00Z"),
        not_after=datetime.fromisoformat("2020-03-30T12:00:00Z"),
    )
    actual = news_in.model_dump(mode="json", by_alias=True)
    assert actual["id"] == "9a6355d0-6d06-11ea-a8da-7b5b9b861935"
    assert datetime.fromisoformat(actual["created"]) == datetime(2020, 3, 23, 6, 38, 34, tzinfo=UTC)
    assert actual["enabled"] is True
    assert actual["type"] == "WARNING"
    assert actual["title"] == "Planned Maintenance Friday Morning"
    assert actual["text"] == "TestText"
    assert datetime.fromisoformat(actual["notBefore"]) == datetime.fromisoformat("2020-03-24T00:00:00Z")
    assert datetime.fromisoformat(actual["notAfter"]) == datetime.fromisoformat("2020-03-30T12:00:00Z")
    assert actual["tags"] == ["MAINTENANCE", "WEBSITE", "CLI"]


def test_news_to_json2() -> None:
    news_in = News(
        id="9a6355d0-6d06-11ea-a8da-7b5b9b861935",
        created=datetime.fromisoformat("2020-03-23T06:38:34Z"),
        enabled=False,
        type="WARNING",
        title="Planned Maintenance Friday Morning",
        text="TestText",
        tags=["MAINTENANCE"],
        not_before=None,
        not_after=None,
    )
    actual = news_in.model_dump(mode="json", by_alias=True)
    assert actual["id"] == "9a6355d0-6d06-11ea-a8da-7b5b9b861935"
    assert datetime.fromisoformat(actual["created"]) == datetime.fromisoformat("2020-03-23T06:38:34Z")
    assert actual["enabled"] is False
    assert actual["type"] == "WARNING"
    assert actual["title"] == "Planned Maintenance Friday Morning"
    assert actual["text"] == "TestText"
    assert actual["tags"] == ["MAINTENANCE"]
    assert "notBefore" not in actual or actual["notBefore"] is None
    assert "notAfter" not in actual or actual["notAfter"] is None


def test_news_to_json3() -> None:
    news_in = News(
        id="9a6355d0-6d06-11ea-a8da-7b5b9b861935",
        created=datetime.fromisoformat("2020-03-23T06:38:34Z"),
        enabled=True,
        type="WARNING",
        title="Planned Maintenance Friday Morning",
        text="TestText",
        tags=[],
        not_before=None,
        not_after=None,
    )
    actual = news_in.model_dump(mode="json", by_alias=True)
    assert actual["id"] == "9a6355d0-6d06-11ea-a8da-7b5b9b861935"
    assert datetime.fromisoformat(actual["created"]) == datetime.fromisoformat("2020-03-23T06:38:34Z")
    assert actual["enabled"] is True
    assert actual["type"] == "WARNING"
    assert actual["title"] == "Planned Maintenance Friday Morning"
    assert actual["text"] == "TestText"
    assert actual["tags"] == []
    assert "notBefore" not in actual or actual["notBefore"] is None
    assert "notAfter" not in actual or actual["notAfter"] is None
