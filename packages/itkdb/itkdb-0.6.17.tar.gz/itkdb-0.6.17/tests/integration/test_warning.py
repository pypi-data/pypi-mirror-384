from __future__ import annotations

import logging

import betamax


def test_get_component(auth_client, caplog):
    with betamax.Betamax(auth_client).use_cassette(
        "test_warnings.test_get_component"
    ), caplog.at_level(logging.WARNING, "itkdb.core"):
        auth_client.get(
            "getComponent", json={"component": "20USE000000086", "ignoreme": "fake"}
        )
        assert "cern-itkpd-main/getComponent/unsupportedKeys" in caplog.text
        assert "ignoreme" in caplog.text
        caplog.clear()


def test_delete_test_property(auth_client, caplog):
    with betamax.Betamax(auth_client).use_cassette(
        "test_testproperties.test_delete_test_property"
    ), caplog.at_level(logging.WARNING, "itkdb.core"):
        # first create, then delete
        auth_client.post(
            "createTestTypeProperty",
            json={
                "id": "603665218f621e000aeada88",
                "code": "TESTDELETEME",
                "name": "Test Delete Me",
                "dataType": "string",
            },
        )
        assert "UuApp::Oidc::Session" in caplog.text
        caplog.clear()

        auth_client.post(
            "deleteTestTypeProperty",
            json={"id": "603665218f621e000aeada88", "code": "TESTDELETEME"},
        )
        assert "UuApp::Oidc::Session" in caplog.text
        caplog.clear()
