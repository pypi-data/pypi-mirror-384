from __future__ import annotations

import pytest

import itkdb


def test_paged_response_falsey(mocker):
    session = mocker.MagicMock()
    response = mocker.MagicMock()
    response.json = mocker.MagicMock(
        return_value={"pageInfo": {"pageIndex": 0, "pageSize": 1000, "total": 0}}
    )

    paged = itkdb.responses.PagedResponse(session, response)
    assert paged.total == 0
    assert paged.page_index == 0
    assert paged.page_size == 1000
    assert not paged


def test_paged_response_truthy(mocker):
    session = mocker.MagicMock()
    response = mocker.MagicMock()
    response.json = mocker.MagicMock(
        return_value={"pageInfo": {"pageIndex": 0, "pageSize": 1000, "total": 1}}
    )

    paged = itkdb.responses.PagedResponse(session, response)
    assert paged.total == 1
    assert paged.page_index == 0
    assert paged.page_size == 1000
    assert paged


@pytest.fixture
def mocked_response(mocker):
    response = mocker.MagicMock()
    response.json = mocker.MagicMock(
        return_value={"pageInfo": {"pageIndex": 0, "pageSize": 1000, "total": 2}}
    )
    response.request.body = (
        '{"pageInfo": {"pageIndex": 0, "pageSize": 1000, "total": 2}}'
    )
    response.request.headers = {"Authorization": "Bearer oldToken"}

    def prepare_auth(auth, _url):
        auth(response.request)

    response.request.prepare_auth = prepare_auth
    response.request.prepare_body = mocker.MagicMock(return_value=None)

    return response


@pytest.fixture
def mocked_session(mocker, mocked_response):
    session = mocker.MagicMock()
    session.send = mocker.MagicMock(return_value=mocked_response)

    def authorize(req):
        req.headers.update({"Authorization": "Bearer newToken"})

    session.authorize = authorize

    return session


def test_paged_response_history(mocked_session, mocked_response):
    paged = itkdb.responses.PagedResponse(mocked_session, mocked_response, history=True)
    assert paged.total == 2
    assert paged.page_index == 0
    assert paged.page_size == 1000
    assert len(paged.pages) == 1
    assert paged

    paged._next_page()
    assert paged.total == 2
    assert paged.page_index == 0
    assert paged.page_size == 1000
    assert len(paged.pages) == 2
    assert paged


def test_paged_response_no_history(mocked_session, mocked_response):
    paged = itkdb.responses.PagedResponse(
        mocked_session, mocked_response, history=False
    )
    assert paged.total == 2
    assert paged.page_index == 0
    assert paged.page_size == 1000
    assert len(paged.pages) == 1
    assert paged

    paged._next_page()
    assert paged.total == 2
    assert paged.page_index == 0
    assert paged.page_size == 1000
    assert len(paged.pages) == 1
    assert paged


def test_paged_response_reauthenticate(mocked_session, mocked_response):
    paged = itkdb.responses.PagedResponse(mocked_session, mocked_response)

    assert paged._response.request.headers["Authorization"] == "Bearer oldToken"

    paged._next_page()
    assert paged._response.request.headers["Authorization"] == "Bearer newToken"


def test_paged_response_empty_body(mocker):
    # define response
    response = mocker.MagicMock()
    response.json = mocker.MagicMock(
        return_value={"pageInfo": {"pageIndex": 0, "pageSize": 1000, "total": 2}}
    )
    response.request.body = None
    response.request.headers = {"Authorization": "Bearer oldToken"}

    def prepare_auth(auth, _url):
        auth(response.request)

    response.request.prepare_auth = prepare_auth
    response.request.prepare_body = mocker.MagicMock(return_value=None)

    # define session
    session = mocker.MagicMock()
    session.send = mocker.MagicMock(return_value=response)

    def authorize(req):
        req.headers.update({"Authorization": "Bearer newToken"})

    session.authorize = authorize

    paged = itkdb.responses.PagedResponse(session, response, history=True)
    assert paged

    paged._next_page()
    assert paged
