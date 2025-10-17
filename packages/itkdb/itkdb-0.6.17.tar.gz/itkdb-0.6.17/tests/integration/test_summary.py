from __future__ import annotations

import betamax


def test_get_summary(auth_session):
    with betamax.Betamax(auth_session).use_cassette("test_summary.test_get_summary"):
        institutes = auth_session.get("listInstitutions")
        assert institutes.status_code == 200
        institutes = institutes.json()
        assert institutes
        assert "pageItemList" in institutes
        assert "pageInfo" in institutes
        assert "uuAppErrorMap" in institutes

        componentTypes = auth_session.get("listComponentTypes", json={"project": "S"})
        assert componentTypes.status_code == 200
        componentTypes = componentTypes.json()
        assert componentTypes
        assert "pageItemList" in componentTypes
        assert "pageInfo" in componentTypes
        assert "uuAppErrorMap" in componentTypes

        for componentType in componentTypes["pageItemList"]:
            test_types = auth_session.get(
                "listTestTypes",
                json={"project": "S", "componentType": componentType["code"]},
            )
            assert test_types.status_code == 200
            test_types = test_types.json()
            assert test_types
            assert "pageItemList" in test_types
            assert "pageInfo" in test_types
            assert "uuAppErrorMap" in test_types
