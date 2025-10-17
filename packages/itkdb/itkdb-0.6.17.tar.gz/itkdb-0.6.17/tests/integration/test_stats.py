from __future__ import annotations

import betamax


def test_get(auth_session):
    with betamax.Betamax(auth_session).use_cassette("test_stats.test_get"):
        response = auth_session.get("getItkpdOverallStatistics")
        assert response.status_code == 200
        response = response.json()
        assert response
        assert "statistics" in response
        assert "uuAppErrorMap" in response
