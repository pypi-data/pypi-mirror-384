from __future__ import annotations

import math

import betamax
import pytest
import requests

import itkdb


def test_client(auth_user):
    assert itkdb.Client(user=auth_user)


def test_client_pagination(auth_client):
    with betamax.Betamax(auth_client).use_cassette("test_institution.test_pagination"):
        response = auth_client.get(
            "listInstitutions", json={"pageInfo": {"pageSize": 5}}
        )
        assert isinstance(response, itkdb.responses.PagedResponse)
        institutes = list(response)
        assert institutes
        assert response.total == 120
        assert len(institutes) == 120
        assert response.limit == 120
        assert response.yielded == 120
        assert response.page_size == 5
        assert response.page_index == math.ceil(120.0 / 5.0) - 1  # 23


# NB: use the same pageSize to make sure we get the same pagination
def test_client_pagination_with_limit(auth_client):
    with betamax.Betamax(auth_client).use_cassette("test_institution.test_pagination"):
        response = auth_client.get(
            "listInstitutions", json={"pageInfo": {"pageSize": 5}}, limit=23
        )
        assert isinstance(response, itkdb.responses.PagedResponse)
        institutes = list(response)
        assert institutes
        assert response.total == 120
        assert len(institutes) == 23
        assert response.limit == 23
        assert response.yielded == 23
        assert response.page_size == 5
        assert response.page_index == math.ceil(23.0 / 5.0) - 1  # 4


# NB: pytest parameterize this
def test_get_component_info_serial(auth_client):
    with betamax.Betamax(auth_client).use_cassette(
        "test_components.test_get_component_info_serial"
    ):
        response = auth_client.get("getComponent", json={"component": "20USE000000086"})
        assert isinstance(response, dict)


def test_prepared_request(auth_client):
    with betamax.Betamax(auth_client).use_cassette(
        "test_components.test_get_component_info_serial"
    ):
        req = requests.Request(
            "GET", "getComponent", json={"component": "20USE000000086"}
        )
        prepped = auth_client.prepare_request(req)
        response = auth_client._response_handler(auth_client.send(prepped))
        assert isinstance(response, dict)


def test_request_handler_called(auth_client, mocker):
    spy = mocker.spy(auth_client, "_request_handler")

    with betamax.Betamax(auth_client).use_cassette(
        "test_components.test_get_component_info_serial"
    ):
        auth_client.get("getComponent", json={"component": "20USE000000086"})

    assert spy.call_count == 1


def test_request_handler_poisonpill(auth_client):
    req = requests.Request(
        "GET", "itkdbPoisonPillTest", json={"component": "20USE000000086"}
    )

    prepped = auth_client.prepare_request(req)

    auth_client._request_handler(prepped)
    assert prepped.url == auth_client._normalize_url("/poison")


def test_request_handler_noop(auth_client):
    req = requests.Request(
        "GET",
        "https://google.com/itkdbPoisonPillTest",
        json={"component": "20USE000000086"},
    )

    prepped = auth_client.prepare_request(req)

    auth_client._request_handler(prepped)

    assert prepped.url == "https://google.com/itkdbPoisonPillTest"


def test_request_handler_createComponentAttachment_noEOS(auth_client):
    image = itkdb.data / "1x1.jpg"

    with image.open("rb") as fp:
        req = requests.Request(
            "POST",
            "createComponentAttachment",
            data={
                "component": "7f633f626f5466b2a72c1be7cd4cb8bc",
                "title": "MyTestAttachment",
                "description": "This is a test attachment descriptor",
                "type": "file",
                "url": image,
            },
            files={"data": (image.name, fp, "image/jpeg")},
        )

        prepped = auth_client.prepare_request(req)

        auth_client._request_handler(prepped)

    assert prepped.url == auth_client._normalize_url("/createComponentAttachment")
    assert prepped.headers.get("content-type") != "application/json"
    assert req.data is not None
    assert req.files is not None
    assert req.json is None
    assert len(prepped.hooks["response"]) == 0


def test_request_handler_createComponentAttachment(auth_client, monkeypatch):
    image = itkdb.data / "1x1.jpg"

    with image.open("rb") as fp:
        req = requests.Request(
            "POST",
            "createComponentAttachment",
            data={
                "component": "7f633f626f5466b2a72c1be7cd4cb8bc",
                "title": "MyTestAttachment",
                "description": "This is a test attachment descriptor",
                "type": "file",
                "url": image,
            },
            files={"data": (image.name, fp, "image/jpeg")},
        )

        monkeypatch.setattr(auth_client, "_use_eos", True)
        prepped = auth_client.prepare_request(req)

        auth_client._request_handler(prepped)

    assert prepped.url == auth_client._normalize_url("/requestUploadEosFile")
    assert prepped.headers.get("content-type") == "application/json"
    assert req.data is None
    assert req.files is None
    assert req.json is not None
    assert len(prepped.hooks["response"]) != 0


def test_duplicate_test_run_exception_no_json(auth_client):
    auth_client._get_duplicate_test_runs = lambda _: ["duplicate_test_run_id"]

    with pytest.raises(ValueError, match="didn't provide any data"):
        auth_client.post("uploadTestRunResults", allow_duplicate=False)

    with pytest.raises(ValueError, match="didn't provide any data"):
        auth_client.post(
            "uploadTestRunResults", data={"key": "value"}, allow_duplicate=False
        )


def test_duplicate_test_run_exception_has_duplicates(auth_client):
    auth_client._get_duplicate_test_runs = lambda _: ["duplicate_test_run_id"]

    with pytest.raises(itkdb.exceptions.DuplicateTestRuns):
        auth_client.post(
            "uploadTestRunResults", json={"key": "value"}, allow_duplicate=False
        )


def test_duplicate_test_run_exception_unsupported_endpoint(auth_client):
    auth_client._get_duplicate_test_runs = lambda _: ["duplicate_test_run_id"]

    with pytest.raises(ValueError, match="No logic exists to check"):
        auth_client.post(
            "fakeRouteNotHandled", json={"key": "value"}, allow_duplicate=False
        )
