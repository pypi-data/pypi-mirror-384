from __future__ import annotations

import logging

import betamax
import pytest

import itkdb


def test_list_test_types(auth_session):
    with betamax.Betamax(auth_session).use_cassette("test_tests.test_list_test_types"):
        response = auth_session.get(
            "listTestTypes", json={"project": "S", "componentType": "HYBRID"}
        )
        assert response.status_code == 200
        response = response.json()
        assert response
        assert "pageItemList" in response
        assert "componentType" in response
        assert "pageInfo" in response
        assert "uuAppErrorMap" in response


def test_create_attachment_image_eos(auth_client, monkeypatch):
    monkeypatch.setattr(auth_client, "_use_eos", True)

    image = itkdb.data / "1x1.jpg"
    with betamax.Betamax(auth_client).use_cassette(
        "test_tests.test_create_attachment_image_eos"
    ):
        testRun_before = auth_client.get(
            "getTestRun",
            json={"testRun": "5dde2c1279bc5c000a61d5e2", "outputType": "object"},
        )

        with image.open("rb") as fp:
            data = {
                "testRun": "5dde2c1279bc5c000a61d5e2",
                "title": "MyTestAttachment",
                "description": "This is a test attachment descriptor",
                "type": "file",
                "url": image,
            }
            attachment = {"data": (image.name, fp, "image/jpeg")}

            auth_client.post("createTestRunAttachment", data=data, files=attachment)

        testRun_after = auth_client.get(
            "getTestRun",
            json={"testRun": "5dde2c1279bc5c000a61d5e2", "outputType": "object"},
        )

        assert len(testRun_after["attachments"]) == 1 + len(
            testRun_before["attachments"]
        )


@pytest.fixture
def duplicate_test_run():
    # checking duplicates for client.get('getTestRun', json={'testRun': '64ef67f09d1c7e0042bfcb0b'})
    return {
        "component": "72b884aab5b0bdf0d39f33f544be485d",
        "stage": "MODULE/ASSEMBLY",
        "testType": "QUAD_MODULE_METROLOGY",
        "runNumber": "1",
        "properties": {"ANALYSIS_VERSION": "1"},
        "results": {
            "PCB_BAREMODULE_POSITION_BOTTOM_LEFT": [2270, 808],
            "PCB_BAREMODULE_POSITION_TOP_RIGHT": [2173, 671],
            "ANGLE_PCB_BM": None,
            "AVERAGE_THICKNESS": [572, 553, 574, 584],
            "STD_DEVIATION_THICKNESS": [2, 2, 1, 1],
            "THICKNESS_VARIATION_PICKUP_AREA": 11,
            "THICKNESS_INCLUDING_POWER_CONNECTOR": 1899,
            "HV_CAPACITOR_THICKNESS": 2269,
        },
        "passed": True,
    }


def test_duplicate_test_run(caplog, auth_client, duplicate_test_run):

    with betamax.Betamax(auth_client).use_cassette(
        "test_tests.test_duplicate_test_run"
    ), caplog.at_level(logging.INFO, "itkdb"):
        test_run_ids = auth_client._get_duplicate_test_runs(duplicate_test_run)
        assert "Found 1 that may be duplicates" in caplog.text

    assert len(test_run_ids) == 1
    assert test_run_ids == ["64ef67f09d1c7e0042bfcb0b"]


@pytest.mark.parametrize(
    ("key", "value", "expectation"),
    [
        ("properties", {"ANALYSIS_VERSION": "2"}, "same properties"),
        ("passed", False, "same passed"),
        ("problems", True, "same problems"),
        ("results", {"new": 2.0}, "same results"),
        ("defects", [{"key": "value"}], "same set of defects"),
        ("comments", ["comment"], "same set of comments"),
    ],
    ids=[
        "properties",
        "passed",
        "problems",
        "parameters",
        "defects",
        "comments",
    ],
)
def test_no_duplicate_test_runs(
    caplog, auth_client, duplicate_test_run, key, value, expectation
):
    duplicate_test_run[key] = value

    with betamax.Betamax(auth_client).use_cassette(
        "test_tests.test_duplicate_test_run"
    ), caplog.at_level(logging.INFO, "itkdb"):
        test_run_ids = auth_client._get_duplicate_test_runs(duplicate_test_run)
        assert expectation in caplog.text

    assert test_run_ids == []
