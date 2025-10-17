from __future__ import annotations

import betamax

import itkdb


def test_urljoin(auth_session):
    assert (
        auth_session._normalize_url("/resource/")
        == "https://itkpd.unicornuniversity.net/resource/"
    )
    assert (
        auth_session._normalize_url("resource/")
        == "https://itkpd.unicornuniversity.net/resource/"
    )
    assert (
        auth_session._normalize_url("/resource")
        == "https://itkpd.unicornuniversity.net/resource"
    )
    assert (
        auth_session._normalize_url("resource")
        == "https://itkpd.unicornuniversity.net/resource"
    )
    assert (
        auth_session._normalize_url("https://itkpd.unicornuniversity.net/resource")
        == "https://itkpd.unicornuniversity.net/resource"
    )
    assert (
        auth_session._normalize_url("https://google.com/resource")
        == "https://google.com/resource"
    )


def test_expires_after(auth_user):
    assert itkdb.core.Session(user=auth_user, expires_after={"days": 1})


def test_no_bearer(auth_session, mocker):
    spy = mocker.spy(auth_session.user, "authenticate")
    with betamax.Betamax(auth_session).use_cassette("test_session.test_no_bearer"):
        response = auth_session.get("https://google.com/")

    assert spy.call_count == 0
    assert "Authorization" not in response.request.headers
