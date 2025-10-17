from __future__ import annotations

import io

import pytest
import requests

import itkdb


def test_true():
    assert True


def test_build_url_utils(mocker):
    request = mocker.MagicMock()
    request.url = "https://itkpd.unicornuniversity.net/createTestRunAttachment"
    request.body = b"abytestring"
    assert (
        itkdb.caching.utils.build_url(request)
        == "https://itkpd.unicornuniversity.net/createTestRunAttachment?&body=abytestring"
    )


def test_pretty_print():
    request = requests.Request(
        "POST",
        "https://stackoverflow.com",
        headers={"User-Agent": "Test"},
        json={"hello": "world"},
    )
    text = itkdb.utils.pretty_print(request)
    assert (
        text
        == 'Host: stackoverflow.com\r\nPOST / HTTP/1.1\r\nUser-Agent: Test\r\nContent-Length: 18\r\nContent-Type: application/json\r\n\r\n{"hello": "world"}'
    )


def test_merge_url():
    assert (
        itkdb.utils.merge_url_query_params(
            "https://itkpd.unicornuniversity.net/createTestRunAttachment",
            {"param1": "value1"},
        )
        == "https://itkpd.unicornuniversity.net/createTestRunAttachment?param1=value1"
    )
    assert (
        itkdb.utils.merge_url_query_params(
            "https://itkpd.unicornuniversity.net/createTestRunAttachment?param2=value2",
            {"param1": "value1"},
        )
        == "https://itkpd.unicornuniversity.net/createTestRunAttachment?param2=value2&param1=value1"
    )


@pytest.mark.parametrize(
    ("fname", "ftype"),
    [
        ("data.txt", "text/plain"),
        ("data.png", "image/png"),
        ("data.root", "application/octet-stream"),
    ],
    ids=["text", "image", "root"],
)
def test_get_file_components(mocker, tmp_path, fname, ftype):
    mocker.patch("magic.from_file", return_value=ftype)
    mocker.patch("requests.utils.guess_filename", return_value=fname)

    fpath = tmp_path / fname
    fpath.write_text("this is a data file")

    fn, fp, ft, fh = itkdb.utils.get_file_components(
        {"data": (fname, fpath.open("rb"), ftype, {"a": "b"})}
    )
    assert fn == fname
    assert isinstance(fp, io.IOBase)
    assert ft == ftype
    assert fh == {"a": "b"}
    fp.close()

    fn, fp, ft, fh = itkdb.utils.get_file_components(
        {"data": (fname, fpath.open("rb"), ftype)}
    )
    assert fn == fname
    assert isinstance(fp, io.IOBase)
    assert ft == ftype
    assert fh == {}
    fp.close()

    fn, fp, ft, fh = itkdb.utils.get_file_components(
        {"data": (fname, fpath.open("rb"))}
    )
    assert fn == fname
    assert isinstance(fp, io.IOBase)
    assert ft == ftype
    assert fh == {}
    fp.close()

    fn, fp, ft, fh = itkdb.utils.get_file_components({"data": fpath.open("rb")})
    assert fn == fname
    assert isinstance(fp, io.IOBase)
    assert ft == ftype
    assert fh == {}
    fp.close()


def test_get_file_components_image_type():
    fname = itkdb.data / "1x1.jpg"
    with fname.open("rb") as fpointer:
        fn, fp, ft, fh = itkdb.utils.get_file_components({"data": fpointer})
        assert ft == "image/jpeg"

    with fname.open(encoding="utf-8") as fpointer:
        fn, fp, ft, fh = itkdb.utils.get_file_components({"data": (fname, fpointer)})
        assert ft == "image/jpeg"


def test_get_file_components_too_many():
    with pytest.raises(
        ValueError, match="creating a single attachment but you specified 2 files"
    ):
        itkdb.utils.get_file_components({"data": None, "another_file": None})


def test_is_image():
    fn = itkdb.data / "1x1.jpg"
    with fn.open("rb") as fp:
        assert itkdb.utils.is_image(str(fn), fp)


def test_is_image_bad_path():
    fn = itkdb.data / "1x1.jpg"
    with fn.open("rb") as fp:
        assert itkdb.utils.is_image("/an/absolutely/fake/path", fp)


def test_is_not_image():
    fn = itkdb.data / "1x1.sh"
    with fn.open("rb") as fp:
        assert not itkdb.utils.is_image(str(fn), fp)


def test_is_root():
    fn = itkdb.data / "tiny.root"
    with fn.open("rb") as fp:
        assert itkdb.utils.is_root(str(fn), fp)


def test_is_not_root():
    fn = itkdb.data / "1x1.jpg"
    with fn.open("rb") as fp:
        assert not itkdb.utils.is_root(str(fn), fp)


@pytest.mark.parametrize(
    ("fpath", "ftype"),
    [
        (itkdb.data / "1x1.jpg", "image/jpeg"),
        (itkdb.data / "1x1.sh", "text/x-shellscript"),
        (itkdb.data / "tiny.root", "application/octet-stream"),
    ],
    ids=["jpeg", "shellscript", "root"],
)
def test_get_mimetype_path(fpath, ftype):
    assert itkdb.utils.get_mimetype(fpath, None) == ftype


@pytest.mark.parametrize(
    ("fpath", "ftype", "mode"),
    [
        (itkdb.data / "1x1.jpg", "image/jpeg", "rb"),
        (itkdb.data / "1x1.sh", "text/x-shellscript", "rb"),
        (itkdb.data / "1x1.sh", "text/x-shellscript", "r"),
        (itkdb.data / "tiny.root", "application/octet-stream", "rb"),
    ],
    ids=["jpeg", "shellscript-binary", "shellscript", "root"],
)
def test_get_mimetype_io(fpath, ftype, mode):
    with fpath.open(mode) as fp:
        assert itkdb.utils.get_mimetype("/an/abs/fake/path", fp) == ftype
        assert fp.tell() == 0


@pytest.mark.parametrize(
    ("fpath", "fsize", "mode"),
    [
        (itkdb.data / "1x1.jpg", 125, "rb"),
        (itkdb.data / "1x1.sh", 820, "rb"),
        (itkdb.data / "1x1.sh", 820, "r"),
        (itkdb.data / "tiny.root", 399, "rb"),
    ],
    ids=["jpeg", "shellscript-binary", "shellscript", "root"],
)
def test_get_filesize(fpath, fsize, mode):
    with fpath.open(mode) as fp:
        assert itkdb.utils.get_filesize(fpath, None) == fsize
        assert itkdb.utils.get_filesize("/an/abs/fake/path", fp) == fsize
        assert fp.tell() == 0
