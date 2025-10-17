from __future__ import annotations

import betamax

import itkdb


def test_get(auth_session):
    with betamax.Betamax(auth_session).use_cassette("test_institution.test_get"):
        response = auth_session.get("listInstitutions")
        assert response.status_code == 200
        response = response.json()
        assert response
        assert "pageItemList" in response
        assert "pageInfo" in response
        assert "uuAppErrorMap" in response
        assert itkdb.models.institution.make_institution_list(response["pageItemList"])
