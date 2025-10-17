from __future__ import annotations

import base64
import gzip
import json
import socket
import time
import uuid
from sys import platform
from urllib.parse import parse_qs, quote, urlparse

import betamax
import pytest
import requests
from betamax_serializers import pretty_json

import itkdb

placeholders = {
    "access_code1": itkdb.settings.ITKDB_ACCESS_CODE1,
    "access_code2": itkdb.settings.ITKDB_ACCESS_CODE2,
}


def filter_requests_record(interaction, current_cassette):
    headers = interaction.data["request"]["headers"]
    bearer_token = headers.get("Authorization")

    eos_token = parse_qs(urlparse(interaction.data["request"]["uri"]).query).get(
        "authz"
    )

    # In cases where we get a large amount of binary data from the server, we'll truncate this.
    if (
        "uu-app-binarystore/getBinaryData" in interaction.data["request"]["uri"]
        and "application/zip"
        not in interaction.data["response"]["headers"]["content-type"]
    ):
        try:
            interaction.data["response"]["body"]["string"] = interaction.data[
                "response"
            ]["body"]["string"][:1000]
        except KeyError:
            interaction.data["response"]["body"]["base64_string"] = interaction.data[
                "response"
            ]["body"]["base64_string"][:1000]

    # Otherwise, create a new placeholder so that when cassette is saved,
    # Betamax will replace the token with our placeholder.
    if bearer_token is not None:
        current_cassette.placeholders.append(
            betamax.cassette.cassette.Placeholder(
                placeholder="Bearer <ACCESS_TOKEN>", replace=bearer_token[0]
            )
        )

    if eos_token is not None:
        current_cassette.placeholders.append(
            betamax.cassette.cassette.Placeholder(
                placeholder="EOS_TOKEN", replace=eos_token[0]
            )
        )
        current_cassette.placeholders.append(
            betamax.cassette.cassette.Placeholder(
                placeholder="EOS_TOKEN", replace=quote(eos_token[0])
            )
        )


def filter_requests_playback(interaction, _):
    # dynamically generate a token for uploading files at a different specific path
    if interaction.data["request"]["uri"].endswith("/requestUploadEosFile"):
        response = interaction.as_response()

        data = response.json()

        eos_path = f"/eos/atlas/test/itkpd/test/itkdb/{uuid.uuid4()}"
        eos_request = requests.post(
            f"https://itkpd2eos.unicornuniversity.net/generate-token?path={eos_path}&permissions=rw"
        )
        eos_token = eos_request.json()["token"]

        data["token"] = eos_token
        data["url"] = f"https://eosatlas.cern.ch{eos_path}"
        enc_data = base64.b64encode(
            gzip.compress(json.dumps(data).encode(response.encoding))
        ).decode()

        interaction.data["response"]["body"]["base64_string"] = enc_data


betamax.Betamax.register_serializer(pretty_json.PrettyJSONSerializer)
with betamax.Betamax.configure() as config:
    config.cassette_library_dir = itkdb.settings.ITKDB_CASSETTE_LIBRARY_DIR
    config.default_cassette_options["serialize_with"] = "prettyjson"
    config.before_record(callback=filter_requests_record)
    config.before_playback(callback=filter_requests_playback)
    for key, value in placeholders.items():
        config.define_cassette_placeholder(f"<{key.upper()}>", replace=value)


@pytest.fixture(scope="session")
def auth_user():
    user = itkdb.core.User()
    user._jwt_options = {
        "verify_signature": False,
        "verify_iat": False,
        "verify_exp": False,
        "verify_aud": False,
    }
    with betamax.Betamax(
        user._session, cassette_library_dir=itkdb.settings.ITKDB_CASSETTE_LIBRARY_DIR
    ).use_cassette("test_user.test_user_good_login", record="none"):
        user.authenticate()
        user._id_token["exp"] = time.time() + 3600
        yield user


@pytest.fixture(scope="module")
def auth_session(auth_user):
    return itkdb.core.Session(user=auth_user)


@pytest.fixture(scope="module")
def auth_client(auth_user):
    return itkdb.Client(user=auth_user)


@pytest.fixture(autouse=True)
def _add_itkdb(doctest_namespace):
    doctest_namespace["itkdb"] = itkdb


# Temporarily work around issue with gethostbyname on OS X
#  - see https://betamax.readthedocs.io/en/latest/long_term_usage.html#known-issues
if platform == "darwin":
    socket.gethostbyname = lambda _: "127.0.0.1"
