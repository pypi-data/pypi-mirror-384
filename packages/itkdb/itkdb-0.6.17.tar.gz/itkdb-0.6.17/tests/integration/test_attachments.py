from __future__ import annotations

import betamax


def test_list_all_attachments(auth_session):
    with betamax.Betamax(auth_session).use_cassette(
        "test_attachments.test_list_all_attachments"
    ):
        response = auth_session.get("uu-app-binarystore/listBinaries")
        assert response.status_code == 200
        response = response.json()
        assert response
        assert "itemList" in response
        assert "pageInfo" in response
        assert "uuAppErrorMap" in response


def test_add_attachment(tmpdir, auth_session):
    temp = tmpdir.join("test.txt")
    temp.write("this is a fake attachment for testing purposes")

    with betamax.Betamax(auth_session).use_cassette(
        "test_attachments.test_add_attachment"
    ):
        component = "20USE000000086"
        title = "this is a test attachment"
        description = "delete this attachment if you see it"
        filename = "test.txt"
        file_type = "text/plain"
        data = {
            "component": component,
            "title": title,
            "description": description,
            "type": "file",
            "url": filename,
        }
        attachment = {"data": (filename, temp, file_type)}
        response = auth_session.post(
            "createComponentAttachment", data=data, files=attachment
        )
        assert response.status_code == 200
        response = response.json()
        assert response
        assert "component" in response
        assert "uuAppErrorMap" in response
        assert "serialNumber" in response["component"]
        assert response["component"]["serialNumber"] == "20USE000000086"
        assert "attachments" in response["component"]
        assert len(response["component"]["attachments"]) > 0

        foundAttachment = False
        for attachment in response["component"]["attachments"]:
            if attachment["filename"] == filename:
                foundAttachment = True
                break

        assert foundAttachment
        assert attachment["title"] == title
        assert attachment["description"] == description
        assert attachment["type"] == "file"
        assert attachment["filename"] == filename
