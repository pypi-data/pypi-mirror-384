from __future__ import annotations

import json
import logging
import pickle
import time

import pytest
import requests

import itkdb

# set some things on user that we expect to persist or not persist
_name = "Test User"
_identity = "Test Identity"
_response = "A response"
_status_code = 200
_access_token = "4cce$$T0k3n"
_raw_id_token = "R4w1DT0k3n"
_access_code1 = "4cce$$C0d31"
_access_code2 = "4cce$$C0d32"


@pytest.fixture
def user_temp(tmp_path):
    temp = tmp_path / "auth.pkl"
    assert temp.exists() is False

    u = itkdb.core.User(
        save_auth=temp,
        access_code1=_access_code1,
        access_code2=_access_code2,
        jwt_options={
            "verify_signature": False,
            "verify_iat": False,
            "verify_aud": False,
        },
    )
    u._name = _name
    u._id_token = {"exp": time.time() + 3600, "name": _name, "uuidentity": _identity}
    u._response = _response
    u._status_code = _status_code
    u._access_token = _access_token
    u._raw_id_token = _raw_id_token
    return u, temp


def test_user_name(user_temp):
    user, _ = user_temp
    assert user.name == _name


def test_user_identity(user_temp):
    user, _ = user_temp
    assert user.identity == _identity


def test_user_expires(user_temp):
    user, _ = user_temp
    assert user.is_authenticated()
    assert user.is_expired() is False
    assert user.expires_in > 0
    user._id_token["exp"] = time.time() - 10
    assert user.is_authenticated()
    assert user.is_expired()
    assert user.expires_in == 0
    user._id_token["exp"] = time.time() + 15
    assert user.is_authenticated()
    assert user.is_expired()
    assert user.expires_in <= 15


def test_user_expires_reauthenticate(user_temp, requests_mock, mocker):
    user, _ = user_temp
    assert user.is_authenticated()
    assert user.is_expired() is False
    assert user.expires_in > 0
    user._id_token["exp"] = time.time() - 1
    assert user.is_authenticated()
    assert user.is_expired()
    assert user.expires_in == 0

    mocker.patch.object(user, "_parse_id_token")
    requests_mock.post(
        requests.compat.urljoin(itkdb.settings.ITKDB_AUTH_URL, "grantToken"),
        text=json.dumps(
            {
                "id_token": {
                    "exp": time.time() + 3600,
                    "name": _name,
                    "uuidentity": _identity,
                },
                "access_token": _access_token,
            }
        ),
    )
    user.authenticate()
    user._id_token = {"exp": time.time() + 3600, "name": _name, "uuidentity": _identity}
    assert user.is_authenticated()
    assert user.is_expired() is False


def test_user_repr(user_temp):
    assert str(user_temp[0])


def test_user_access_codes(user_temp):
    assert user_temp[0].access_code1 == _access_code1
    assert user_temp[0].access_code2 == _access_code2


def test_user_unpicklable(user_temp, caplog):
    user, temp = user_temp
    session = itkdb.core.Session(user=user)
    assert temp.exists() is False
    with caplog.at_level(logging.INFO, "itkdb"):
        # inject an unpicklable object
        session.user.fake = lambda x: x
        session.user._dump()
        assert "Unable to save user session to" in caplog.text


def test_user_serialization(user_temp, caplog):
    user, temp = user_temp
    # set up first user and check that we can dump
    session = itkdb.core.Session(user=user)
    assert temp.exists() is False
    assert session.user._dump()
    assert temp.exists()
    assert temp.stat().st_size
    with user._save_auth.open("rb") as fp:
        assert pickle.load(fp)

    # check if we can reload user
    session.user._id_token = None
    assert session.user._load()
    assert session.user.name == _name
    del session

    # check if session can load user
    session = itkdb.core.Session(user=user, save_auth=temp)
    assert session.user.name == _name
    assert session.user._session
    assert session.user._response == _response
    assert session.user._status_code == _status_code
    assert session.user._access_token == _access_token
    assert session.user._raw_id_token == _raw_id_token

    # check what happens if the saved user has expired
    session.user._id_token["exp"] = time.time() + 4 + session.user.auth_expiry_threshold
    session.user._dump()
    time.sleep(5)
    with caplog.at_level(logging.INFO, "itkdb"):
        assert session.user._load() is False
        assert "Saved user session is expired in" in caplog.text
    del session

    # check what happens if corruption
    temp.write_text("fake")
    with caplog.at_level(logging.INFO, "itkdb"):
        user = itkdb.core.User(save_auth=temp)
        assert "Unable to load user session" in caplog.text
        caplog.clear()
        assert user._load() is False
        assert "Unable to load user session" in caplog.text
        caplog.clear()
        itkdb.core.Session(save_auth=temp)
        assert "Unable to load user session" in caplog.text
