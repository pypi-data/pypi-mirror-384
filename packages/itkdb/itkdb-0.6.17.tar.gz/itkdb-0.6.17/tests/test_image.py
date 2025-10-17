from __future__ import annotations

import pytest

import itkdb


@pytest.fixture
def response(mocker):
    response = mocker.MagicMock()
    response.headers = {"content-disposition": "inline; filename=myfilename.ext"}
    response.iter_content = mocker.MagicMock(
        return_value=iter([b"Some binary content that pretends to be an image"])
    )
    return response


def test_make_image(response):
    image = itkdb.models.ImageFile.from_response(response)
    assert isinstance(image, itkdb.models.ImageFile)
    assert image.suggested_filename == "myfilename.ext"
    assert len(image) == 48
    assert image.size == 48


def test_save_image(tmp_path, response):
    image = itkdb.models.ImageFile.from_response(response)
    temp = tmp_path.joinpath("saved_image.jpg")
    nbytes = image.save(filename=temp)
    assert nbytes == 48
    assert temp.stat().st_size == 48
