from __future__ import annotations

import logging

import betamax

import itkdb


def test_get_image(auth_session):
    with betamax.Betamax(auth_session).use_cassette("test_binaryData.test_get_image"):
        response = auth_session.get(
            "uu-app-binarystore/getBinaryData",
            json={
                "code": "bc2eccc58366655352582970d3f81bf46f15a48cf0cb98d74e21463f1dc4dcb9"
            },
        )
        assert response
        assert response.status_code == 200
        assert response.headers.get("content-type").startswith("image")


def test_get_image_model(auth_client, tmpdir):
    with betamax.Betamax(auth_client).use_cassette("test_binaryData.test_get_image"):
        image = auth_client.get(
            "uu-app-binarystore/getBinaryData",
            json={
                "code": "bc2eccc58366655352582970d3f81bf46f15a48cf0cb98d74e21463f1dc4dcb9"
            },
        )
        assert isinstance(image, itkdb.models.ImageFile)
        assert image.suggested_filename == "PB6.CR2"
        assert image.extension == "cr2"
        temp = tmpdir.join("saved_image.cr2")
        nbytes = image.save(filename=temp.strpath)
        assert nbytes == 1166


def test_get_plain_text(auth_session):
    with betamax.Betamax(auth_session).use_cassette(
        "test_binaryData.test_get_plainText"
    ):
        response = auth_session.get(
            "uu-app-binarystore/getBinaryData",
            json={
                "code": "5fd40be3b9f9ada57fa47fe4d8b3c48b26055d5d1c6306d76eb2181d20089879"
            },
        )
        assert response
        assert response.status_code == 200
        assert response.headers.get("content-type").startswith("text")


def test_get_plain_text_model(auth_client, tmpdir):
    with betamax.Betamax(auth_client).use_cassette(
        "test_binaryData.test_get_plainText"
    ):
        text = auth_client.get(
            "uu-app-binarystore/getBinaryData",
            json={
                "code": "5fd40be3b9f9ada57fa47fe4d8b3c48b26055d5d1c6306d76eb2181d20089879"
            },
        )
        assert isinstance(text, itkdb.models.TextFile)
        assert text.suggested_filename == "for_gui test3.txt"
        assert text.extension == "txt"
        temp = tmpdir.join("saved_text.txt")
        nbytes = text.save(filename=temp.strpath)
        assert nbytes == 23


def test_get_json(auth_session):
    with betamax.Betamax(auth_session).use_cassette("test_binaryData.test_get_json"):
        response = auth_session.get(
            "uu-app-binarystore/getBinaryData",
            json={"code": "54fc652d3e2f745ea15bc612b4f2b16d"},
        )
        assert response
        assert response.status_code == 200
        assert response.headers.get("content-type") == "application/json"


def test_get_json_model(auth_client, tmpdir):
    with betamax.Betamax(auth_client).use_cassette("test_binaryData.test_get_json"):
        text = auth_client.get(
            "uu-app-binarystore/getBinaryData",
            json={"code": "54fc652d3e2f745ea15bc612b4f2b16d"},
        )
        assert isinstance(text, itkdb.models.TextFile)
        assert text.suggested_filename == "644ecb882d292775dfcf0ec3.json"
        assert text.extension == "json"
        temp = tmpdir.join("saved_json.json")
        nbytes = text.save(filename=temp.strpath)
        assert nbytes == 896


def test_issue4(auth_session):
    with betamax.Betamax(auth_session).use_cassette("test_binaryData.test_issue4"):
        response = auth_session.get(
            "uu-app-binarystore/getBinaryData",
            json={
                "code": "fe4f85dd3740c53956c22bb4324065b8",
                "contentDisposition": "attachment",
            },
        )
        assert response
        assert response.status_code == 200
        assert response.headers.get("content-type").startswith("text")


def test_issue4_model(auth_client, tmpdir):
    with betamax.Betamax(auth_client).use_cassette("test_binaryData.test_issue4"):
        text = auth_client.get(
            "uu-app-binarystore/getBinaryData",
            json={
                "code": "fe4f85dd3740c53956c22bb4324065b8",
                "contentDisposition": "attachment",
            },
        )
        assert isinstance(text, itkdb.models.TextFile)
        assert text.suggested_filename == "VPA37913-W00221_Striptest_Segment_4_001.dat"
        assert text.extension == "dat"
        temp = tmpdir.join("saved_text.dat")
        nbytes = text.save(filename=temp.strpath)
        assert nbytes == 1000


def test_get_zipfile(auth_session):
    with betamax.Betamax(auth_session).use_cassette(
        "test_binaryData.test_get_zipfile", preserve_exact_body_bytes=True
    ):
        response = auth_session.get(
            "uu-app-binarystore/getBinaryData",
            json={"code": "143b2c7182137ff619968f4cc41a18ca"},
        )
        assert response
        assert response.status_code == 200
        assert response.headers.get("content-type").startswith("application/zip")
        assert len(response.content) == 226988


def test_get_zipfile_model(auth_client, tmpdir):
    with betamax.Betamax(auth_client).use_cassette("test_binaryData.test_get_zipfile"):
        zipfile = auth_client.get(
            "uu-app-binarystore/getBinaryData",
            json={"code": "143b2c7182137ff619968f4cc41a18ca"},
        )
        assert isinstance(zipfile, itkdb.models.ZipFile)
        assert zipfile.suggested_filename == "configuration_MODULETHERMALCYCLING.zip"
        assert zipfile.extension == "zip"
        assert zipfile.size == 226988
        assert zipfile.size_fmt == "221.7KiB"
        temp = tmpdir.join("saved_zipfile.zip")
        nbytes = zipfile.save(filename=temp.strpath)
        assert nbytes == 226988


def test_get_image_model_eos(tmpdir, auth_client, caplog):
    with betamax.Betamax(auth_client).use_cassette(
        "test_binaryData.test_get_image_model_eos", preserve_exact_body_bytes=True
    ):
        auth = auth_client.post(
            "https://itkpd2eos.unicornuniversity.net/generate-token?path=/eos/atlas/test/itkpd/c/c/c/cccac749f4f3d5e493a0186ca9e42803"
        )

        # NB: this will not work if you want to try to spy it
        # spy = mocker.spy(super(auth_client.__class__, auth_client).get, "__func__")
        with caplog.at_level(logging.INFO, "itkdb.client"):
            image = auth_client.get(
                f'https://eosatlas.cern.ch/eos/atlas/test/itkpd/c/c/c/cccac749f4f3d5e493a0186ca9e42803?authz={auth["token"]}',
            )
            assert (
                "Identified a cern.ch request, will attach CERN SSL chain to request by overriding `verify`"
                in caplog.text
            )
            assert (
                "Identified a request that potentially downloads larger amounts of data, will execute chunked requests (stream=True)"
                in caplog.text
            )
            assert (
                "Changing the mimetype for the response from EOS from 'application/octet-stream' to 'image/jpeg'"
                in caplog.text
            )

        assert isinstance(image, itkdb.models.ImageFile)
        assert image.suggested_filename is None
        assert image.extension == "jpg"
        temp = tmpdir.join("saved_image.jpg")
        nbytes = image.save(filename=temp.strpath)
        assert nbytes == 125


def test_get_empty_file(tmpdir, auth_client, caplog):
    path = "/eos/atlas/atlascerngroupdisk/det-itk/prod-db/0/6/1/06109d5eca7badf9df40562fcb449460"

    with betamax.Betamax(auth_client).use_cassette(
        "test_binaryData.test_get_empty_file", preserve_exact_body_bytes=True
    ):
        auth = auth_client.post(
            f"https://itkpd2eos.unicornuniversity.net/generate-token?path={path}"
        )

        # NB: this will not work if you want to try to spy it
        # spy = mocker.spy(super(auth_client.__class__, auth_client).get, "__func__")
        with caplog.at_level(logging.INFO, "itkdb.client"):
            attachment = auth_client.get(
                f'https://eosatlas.cern.ch{path}?authz={auth["token"]}',
            )
            assert (
                "No mimetype available. This is likely an empty file. Defaulting to BinaryFile."
                in caplog.text
            )

        assert isinstance(attachment, itkdb.models.BinaryFile)
        assert attachment.suggested_filename is None
        assert attachment.extension is None
        temp = tmpdir.join("saved_empty_attachment")
        nbytes = attachment.save(filename=temp.strpath)
        assert nbytes == 0
