from __future__ import annotations

import betamax

import itkdb


def test_create_attachment_image_eos(auth_client, monkeypatch):
    monkeypatch.setattr(auth_client, "_use_eos", True)

    image = itkdb.data / "1x1.jpg"
    with betamax.Betamax(auth_client).use_cassette(
        "test_shipments.test_create_attachment_image_eos"
    ):
        shipment_before = auth_client.get(
            "getShipment", json={"shipment": "61149203db062f000b98a75a"}
        )

        with image.open("rb") as fp:
            data = {
                "shipment": "61149203db062f000b98a75a",
                "title": "MyTestAttachment",
                "description": "This is a test attachment descriptor",
                "type": "file",
                "url": image,
            }
            attachment = {"data": (image.name, fp, "image/jpeg")}

            auth_client.post("createShipmentAttachment", data=data, files=attachment)

        shipment_after = auth_client.get(
            "getShipment", json={"shipment": "61149203db062f000b98a75a"}
        )

        assert len(shipment_after["attachments"]) == 1 + len(
            shipment_before["attachments"]
        )
