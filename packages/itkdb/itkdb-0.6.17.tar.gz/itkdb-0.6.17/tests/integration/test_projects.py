from __future__ import annotations

import betamax


def test_list_projects(auth_session):
    with betamax.Betamax(auth_session).use_cassette("test_projects.test_list_projects"):
        response = auth_session.get("listProjects")
        assert response.status_code == 200
        response = response.json()
        assert response
        assert "itemList" in response
        assert "pageInfo" in response
        assert "uuAppErrorMap" in response
