from __future__ import annotations

import betamax

import itkdb


def test_get(auth_session):
    with betamax.Betamax(auth_session).use_cassette("test_components.test_get"):
        response = auth_session.get("listComponentTypes", json={"project": "S"})
        assert response.status_code == 200
        response = response.json()
        assert response
        assert "pageItemList" in response
        assert "pageInfo" in response
        assert "uuAppErrorMap" in response


def test_list_componentsv1(auth_session):
    with betamax.Betamax(auth_session).use_cassette(
        "test_components.test_list_componentsv1"
    ):
        response = auth_session.get("listComponents", json={"project": "S"})
        assert response.status_code == 200
        response = response.json()
        assert response
        assert "pageItemList" in response
        assert "pageInfo" in response
        assert "uuAppErrorMap" in response


def test_list_components_componentTypev1(auth_session):
    with betamax.Betamax(auth_session).use_cassette(
        "test_components.test_list_components_componentTypev1"
    ):
        response = auth_session.get(
            "listComponents", json={"project": "S", "componentType": "HYBRID"}
        )
        assert response.status_code == 200
        response = response.json()
        assert response
        assert "pageItemList" in response
        assert "pageInfo" in response
        assert "uuAppErrorMap" in response


def test_list_componentsv2(auth_session):
    with betamax.Betamax(auth_session).use_cassette(
        "test_components.test_list_componentsv2"
    ):
        response = auth_session.get(
            "listComponents", json={"filterMap": {"project": "S"}}
        )
        assert response.status_code == 200
        response = response.json()
        assert response
        assert "itemList" in response
        assert "pageInfo" in response
        assert "uuAppErrorMap" in response


def test_list_components_componentTypev2(auth_session):
    with betamax.Betamax(auth_session).use_cassette(
        "test_components.test_list_components_componentTypev2"
    ):
        response = auth_session.get(
            "listComponents",
            json={"filterMap": {"project": "S", "componentType": "HYBRID"}},
        )
        assert response.status_code == 200
        response = response.json()
        assert response
        assert "itemList" in response
        assert "pageInfo" in response
        assert "uuAppErrorMap" in response


# NB: pytest parameterize this
def test_get_component_info_serial(auth_session):
    with betamax.Betamax(auth_session).use_cassette(
        "test_components.test_get_component_info_serial"
    ):
        response = auth_session.get(
            "getComponent", json={"component": "20USE000000086"}
        )
        assert response.status_code == 200
        response = response.json()
        assert response
        assert "uuAppErrorMap" in response


def test_get_component_info_code(auth_session):
    with betamax.Betamax(auth_session).use_cassette(
        "test_components.test_get_component_info_code"
    ):
        response = auth_session.get(
            "getComponent", json={"component": "54f134b9975bebc851c4671d0ccbb489"}
        )
        assert response.status_code == 200
        response = response.json()
        assert response
        assert "uuAppErrorMap" in response


def test_get_component_bulk(auth_session):
    with betamax.Betamax(auth_session).use_cassette(
        "test_components.test_get_component_bulk"
    ):
        response = auth_session.get(
            "getComponentBulk", json={"component": ["54f134b9975bebc851c4671d0ccbb489"]}
        )
        assert response.status_code == 200
        response = response.json()
        assert response
        assert "uuAppErrorMap" in response
        assert "pageInfo" not in response
        assert "itemList" in response


def test_get_component_bulk_client(auth_client):
    with betamax.Betamax(auth_client).use_cassette(
        "test_components.test_get_component_bulk"
    ):
        response = auth_client.get(
            "getComponentBulk", json={"component": ["54f134b9975bebc851c4671d0ccbb489"]}
        )
        assert response
        assert isinstance(response, list)


def test_add_comment(auth_session):
    with betamax.Betamax(auth_session).use_cassette("test_components.test_add_comment"):
        component = "20USE000000086"
        message = "this is a test message"
        data = {"component": component, "comments": [message]}
        response = auth_session.post("createComponentComment", json=data)
        assert response.status_code == 200
        response = response.json()
        assert response
        assert "component" in response
        assert "uuAppErrorMap" in response
        assert "serialNumber" in response["component"]
        assert response["component"]["serialNumber"] == "20USE000000086"
        assert "comments" in response["component"]
        assert len(response["component"]["comments"]) > 0

        foundComment = False
        for comment in response["component"]["comments"]:
            if comment["comment"] == message:
                foundComment = True
                break

        assert foundComment


# https://uuapp.plus4u.net/uu-bookkit-maing01/78462435-41f76117152c4c6e947f498339998055/book/page?code=41219994
def test_create_attachment_image_eos(auth_client, monkeypatch):
    monkeypatch.setattr(auth_client, "_use_eos", True)

    image = itkdb.data / "1x1.jpg"
    with betamax.Betamax(auth_client).use_cassette(
        "test_components.test_create_attachment_image_eos"
    ):
        component_before = auth_client.get(
            "getComponent", json={"component": "7f633f626f5466b2a72c1be7cd4cb8bc"}
        )

        with image.open("rb") as fp:
            data = {
                "component": "7f633f626f5466b2a72c1be7cd4cb8bc",
                "title": "MyTestAttachment",
                "description": "This is a test attachment descriptor",
                "type": "file",
                "url": image,
            }
            attachment = {"data": (image.name, fp, "image/jpeg")}

            auth_client.post("createComponentAttachment", data=data, files=attachment)

        component_after = auth_client.get(
            "getComponent", json={"component": "7f633f626f5466b2a72c1be7cd4cb8bc"}
        )

        assert len(component_after["attachments"]) == 1 + len(
            component_before["attachments"]
        )


def test_delete_attachment_image_eos(auth_client, monkeypatch):
    monkeypatch.setattr(auth_client, "_use_eos", True)

    image = itkdb.data / "1x1.jpg"
    with betamax.Betamax(auth_client).use_cassette(
        "test_components.test_delete_attachment_image_eos"
    ):
        component_before = auth_client.get(
            "getComponent", json={"component": "7f633f626f5466b2a72c1be7cd4cb8bc"}
        )

        with image.open("rb") as fp:
            data = {
                "component": "7f633f626f5466b2a72c1be7cd4cb8bc",
                "title": "MyTestAttachment",
                "description": "This is a test attachment descriptor",
                "type": "file",
                "url": image,
            }
            attachment = {"data": (image.name, fp, "image/jpeg")}

            attachment_new = auth_client.post(
                "createComponentAttachment", data=data, files=attachment
            )

        component_after = auth_client.get(
            "getComponent", json={"component": "7f633f626f5466b2a72c1be7cd4cb8bc"}
        )

        assert len(component_after["attachments"]) == 1 + len(
            component_before["attachments"]
        )

        auth_client.post(
            "deleteComponentAttachment",
            json={
                "component": "7f633f626f5466b2a72c1be7cd4cb8bc",
                "code": attachment_new["code"],
            },
        )

        component_after = auth_client.get(
            "getComponent", json={"component": "7f633f626f5466b2a72c1be7cd4cb8bc"}
        )

        assert len(component_after["attachments"]) == len(
            component_before["attachments"]
        )
