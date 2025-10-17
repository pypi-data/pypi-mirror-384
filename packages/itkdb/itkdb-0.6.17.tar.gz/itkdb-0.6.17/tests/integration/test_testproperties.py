from __future__ import annotations

import betamax


# this also checks that we handle the warning as string properly in test_warnings
def test_delete_test_property(auth_client):
    with betamax.Betamax(auth_client).use_cassette(
        "test_testproperties.test_delete_test_property"
    ):
        # first create, then delete
        response = auth_client.post(
            "createTestTypeProperty",
            json={
                "id": "603665218f621e000aeada88",
                "code": "TESTDELETEME",
                "name": "Test Delete Me",
                "dataType": "string",
            },
        )
        assert response

        response = auth_client.post(
            "deleteTestTypeProperty",
            json={"id": "603665218f621e000aeada88", "code": "TESTDELETEME"},
        )
        assert response
