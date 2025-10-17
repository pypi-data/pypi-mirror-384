from __future__ import annotations

import logging

import betamax
import pytest

import itkdb

# because expiration will fail (since we cache this information) skip the verification of expiration
jwt_options = {
    "verify_signature": False,
    "verify_iat": False,
    "verify_exp": False,
    "verify_aud": False,
}


def test_user_create():
    user = itkdb.core.User(access_code1="foo", access_code2="bar")
    assert user.access_token is None
    assert not user.bearer
    assert user.id_token == {}
    assert not user.name
    assert user.expires_at == 0
    assert user.expires_in == 0
    assert user.is_expired()


# NB: because we are using betamax - the ID token which is invalid after 2
# hours is kept so user.is_expired() will be true for testing, do not assert it
def test_user_anonymous_login():
    user = itkdb.core.User(access_code1="", access_code2="", jwt_options=jwt_options)
    with betamax.Betamax(user._session).use_cassette(
        "test_user.test_user_anonymous_login"
    ):
        with pytest.raises(itkdb.exceptions.ResponseException):
            user.authenticate()
        assert user.is_authenticated() is False
        assert user._response is not None
        assert user._response.status_code == 500


def test_user_bad_login():
    user = itkdb.core.User(
        access_code1="foo", access_code2="bar", jwt_options=jwt_options
    )
    with betamax.Betamax(user._session).use_cassette("test_user.test_user_bad_login"):
        with pytest.raises(itkdb.exceptions.ResponseException):
            user.authenticate()
        assert user.is_authenticated() is False
        assert user._response is not None
        assert user._response.status_code == 401


# NB: because we are using betamax - the ID token which is invalid after 2
# hours is kept so user.is_expired() will be true for testing, do not assert it
def test_user_good_login(caplog):
    user = itkdb.core.User(jwt_options=jwt_options)
    with betamax.Betamax(user._session).use_cassette("test_user.test_user_good_login"):
        with caplog.at_level(logging.INFO, "itkdb"):
            user.authenticate()
            assert not caplog.text
        assert user.is_authenticated()
        assert user._response


def test_user_identity():
    user = itkdb.core.User(jwt_options=jwt_options)
    with betamax.Betamax(user._session).use_cassette("test_user.test_user_good_login"):
        user.authenticate()
        assert user.identity
