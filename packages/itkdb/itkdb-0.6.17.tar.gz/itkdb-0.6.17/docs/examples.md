# Examples

---

## Information about yourself

```py
import itkdb

client = itkdb.Client()
client.user.authenticate()  # (1)!
user = client.get("getUser", json={"userIdentity": client.user.identity})
print([institution["code"] for institution in user["institutions"]])
# ['UCSC', ...]
```

1. If you have not made any requests to the database using the `client` in the
   current session, you need to manually call [itkdb.core.User.authenticate][]
   to instantiate details about the user.

## Information about another user

```py
import itkdb

client = itkdb.Client()
user = client.get("getUser", json={"userIdentity": "23-2145-1"})
print([institution["code"] for institution in user["institutions"]])
# ['UCSC', 'IHEP', 'UBC', 'UCSC_STRIP_SENSORS']
```

## Getting a component

```py
import itkdb

client = itkdb.Client()
component = client.get("getComponent", json={"component": "20USBSX0000421"})  # (1)!
print(f"code={component['code']}, sn={component['serialNumber']}")
# code=0b7346e49f2c2d6153fb940e20da4978, sn=20USBSX0000421
```

1. You can also get a component by it's mongo
   [ObjectId](https://www.mongodb.com/docs/manual/reference/method/ObjectId/),
   or alternative identifier.

## Checking if component exists

```py
import itkdb

c = itkdb.Client()
sn = "DOESNOTEXIST"
try:
    comp = c.get("getComponent", json={"component": sn})
except itkdb.exceptions.BadRequest as exc:  # (1)!
    if (
        "ucl-itkpd-main/getComponent/componentDoesNotExist" in exc.response.json()
    ):  # (2)!
        msg = f"component with serial number {sn} does not exist."
        raise KeyError(msg)  # (3)!
    raise
```

1. `itkdb` will raise a [itkdb.exceptions.BadRequest][] exception which will happen in the case of trying to get a component that does not exist.
2. It might not always be the case that one receives a `BadRequest` due to a missing component, but could be some other reason. Here, we check information in the `uuAppErrorMap` to understand what error(s) actually happened.
3. We raise a `KeyError` that's specific to your application, but you can certainly do any other logic you would like here.


## Using the cache

By default, [itkdb.core.Session][] instances have `use_cache=True`. What this
means is that when the API responds with information in the headers about the
ability to cache the result, `itkdb` will do its best to follow the
[HTTP Caching spec](https://httpwg.org/specs/rfc9111.html) and automatically
cache where instructed to. If you're not sure what caching is, please refer to
the
[Mozilla Web Docs](https://developer.mozilla.org/en-US/docs/Web/HTTP/Caching)
for a gentler introduction to HTTP caching.

In many cases, however, the Production Database API does not instruct us to
cache so `itkdb` provides a way to override this. In order to force (override)
the headers, one can specify how long a particular request should be cached for
using the `expires_after` keyword as shown below.

```py
import itkdb

c = itkdb.Client(expires_after=dict(days=1))  # (1)!
c.get("listInstitutions")  # (2)!
assert c._response.from_cache == False
c.get("listInstitutions")  # (3)!
assert c._response.from_cache == True
```

1. We will set the expiry to 1 day. This uses the same structure as
   [datetime.timedelta](https://docs.python.org/3/library/datetime.html#timedelta-objects)
   from python's standard library, so `days`, `seconds`, `weeks`, etc.
2. Simply perform any request operation that should be cache-able, such as `GET`
   requests. The first time the request is made, it will not be cached.
3. The next time you make the same request within the expiry time, it will pull
   your request from the cache automatically.

## Retrieving a list of components

This example shows how to iterate through components, requesting 32 components
from the database at a time:

```py
import itkdb

client = itkdb.Client()

data = {"filterMap": {"project": "P"}, "pageInfo": {"pageSize": 32}}  # (1)!
components_pixels = client.get("listComponents", json=data)  # (2)!

print(components_pixels.total)  # (3)!

for component in components_pixels:  # (4)!
    if j > 5:
        break  # do not print thousands of components
    print(component["code"])
```

1. Each page retrieved from the database will have at most 32 components.
   Strictly speaking, every page but the last page will be guaranteed to have 32
   components.
2. For any request from the database that retrieves a list of items, such as
   `listComponents` or `listInstitutions`, the response typically is paginated
   (wrapped in a `"pageItemList"` key). The [itkdb.Client][] returns a
   [itkdb.responses.PagedResponse][] object that helps deal with the pagination
   by automatically retrieving more pages for you as needed. This line only
   loads the first page (a single HTTP request is made).
3. There's a lot of metadata stored on the [itkdb.responses.PagedResponse][]
   object that is useful for inspection without having to make additional
   requests.
4. [itkdb.responses.PagedResponse][] can be treated like an iterable in python
   and you can just simply iterate over it. As you iterate and exhaust items on
   the currently fetched page, it will automatically make another HTTP request
   to fetch the next page for you (if there is one), or stop the iteration once
   you've reached the limit of items.

## Retrieve test type information from component

Information on the type of tests which have been uploaded to a component in the
database is accessible from the component object.

```py
import itkdb

client = itkdb.Client()
component = client.get("getComponent", json={"component": "20USBSX0000421"})  # (1)!
component["tests"]  # (2)!
[print(f"{x['name']}: {len(x['testRuns'])}") for x in component["tests"]]
# Manufacturing Data ATLAS18: 1
# ATLAS18 IV Test V1: 1
# ATLAS18 CV Test V1: 1
# ATLAS18 Visual Inspection V2: 1
```

1. Retrieve component information (as above)
2. Test type information part of returned object

## Retrieve a test run

Test data is retrieved from _testRun_ objects stored in the database and
associated with a component. Test data is retrieved by two queries: the first
retrieves the test _id_ which is used to identify the testRun object; the second
retrieves the test run results.

```py
import itkdb

client = itkdb.Client()
component = client.get("getComponent", json={"component": "20USBSX0000421"})  # (1)!
testID = [
    y["id"]
    for x in component["tests"]
    for y in x["testRuns"]
    if x["name"] == "ATLAS18 Visual Inspection V2"
]  # (2)!
print(testID)
# 610a7774124ef4000aeee6c9
testRun = client.get("getTestRun", json={"testRun": testID[0]})  # (3)!
print(f"testRun id={testRun['id']}, of testType:{testRun['testType']['name']}")
# testRun id=610a7774124ef4000aeee6c9, of testType:ATLAS18 Visual Inspection V2
```

1. Retrieve component information
2. Select particular test run of test type: ATLAS18 Visual Inspection V2
3. Retrieve test data by mongo
   [ObjectId](https://www.mongodb.com/docs/manual/reference/method/ObjectId/)
   only

## Retrieve multiple tests

Retrieval of test run data can be scaled up using a _bulk_ query. In this case
an array of test _id_ s is used to retrieve corresponding test data.

```py
import itkdb

client = itkdb.Client()
component = client.get("getComponent", json={"component": "20USBSX0000421"})  # (1)!
testID = [y["id"] for x in component["tests"] for y in x["testRuns"]]  # (2)!
print(testID)
# ['5f87c40e50d75e000a33281c', '5f902b121a9458000a97c30c', '5f902b0e1a9458000a97c2f8', '610a7774124ef4000aeee6c9']
testRuns = client.get("getTestRunBulk", json={"testRun": testID})  # (3)!
print(f"testRuns found: {len(testRuns)}")
# testRuns found: 4
```

1. Retrieve component information
2. Select set of test runs - same or various types
3. Retrieve test data by mongo
   [ObjectId](https://www.mongodb.com/docs/manual/reference/method/ObjectId/)s
   only

## Download an attachment from ITkPD

Downloading an attachment from the database is relatively straightforward. When
using [itkdb.Client][] (and not [itkdb.core.Session][]), the response will
automatically be converted to a [itkdb.models.BinaryFile][]-like object. All
`BinaryFile` have the same baseline set of functionality, with additional
helpers specific to the type of attachment (or file) that has been downloaded
(such as [itkdb.models.ImageFile][] or [itkdb.models.TextFile][]).

In order to reduce the memory overhead, these attachments are ephemeral
(temporarily saved to disk). If you need to persist longer, you can use the
corresponding `attachment.save()` function (see
[itkdb.models.file.BinaryFile.save][]).

=== "Image"

    ```py
    import itkdb

    client = itkdb.Client()

    data = {"component": component_code, "code": attachment_code}

    attachment = client.get("getComponentAttachment", json=data)  # (1)!
    attachment  # <itkdb.models.file.ImageFile(....) file-like object at TMP_PATH> (2)
    attachment.mimetype  # 'image/x-canon-cr2' (3)
    attachment.content_type  # 'image/x-canon-cr2' (4)
    attachment.extension  # 'cr2' (5)
    attachment.filename  # 'TMP_PATH' (6)
    attachment.suggested_filename  # 'PB6.CR2' (7)
    attachment.size  # 35819362 (8)
    attachment.size_fmt  # '34.2MiB' (9)

    attachment.save()  # saves to disk (10)
    ```

    1. This is an [itkdb.models.ImageFile][].
    2. The attachment object
    3. The mimetype of the content from the response headers
    4. The mimetype of the content using [itkdb.utils.get_mimetype][]
    5. The extension of the file
    6. The filename of the ephemeral file on disk
    7. The filename extracted from the response headers (may not have one!)
    8. The size of the file in bytes
    9. The human-readable size of the file
    10. If no path is specified, will use `suggested_filename` and save to current working directory.

=== "Text"

    ```py
    import itkdb

    client = itkdb.Client()

    data = {"shipment": shipment_code, "code": attachment_code}

    attachment = client.get("getShipmentAttachment", json=data)  # (1)!
    attachment  # <itkdb.models.file.TextFile(....) file-like object at TMP_PATH> (2)
    attachment.mimetype  # 'text/plain; charset=UTF-8' (3)
    attachment.content_type  # 'text/plain' (4)
    attachment.extension  # 'txt' (5)
    attachment.filename  # 'TMP_PATH' (6)
    attachment.suggested_filename  # 'for_gui test3.txt' (7)
    attachment.size  # 23 (8)
    attachment.size_fmt  # '23.0B' (9)

    attachment.save()  # saves to disk (10)
    ```

    1. This is an [itkdb.models.TextFile][].
    2. The attachment object
    3. The mimetype of the content from the response headers
    4. The mimetype of the content using [itkdb.utils.get_mimetype][]
    5. The extension of the file
    6. The filename of the ephemeral file on disk
    7. The filename extracted from the response headers (may not have one!)
    8. The size of the file in bytes
    9. The human-readable size of the file
    10. If no path is specified, will use `suggested_filename` and save to current working directory.

=== "Zip"

    ```py
    import itkdb

    client = itkdb.Client()

    data = {"testRun": test_run_code, "code": attachment_code}

    attachment = client.get("getTestRunAttachment", json=data)  # (1)!
    attachment  # <itkdb.models.file.ZipFile(....) file-like object at TMP_PATH> (2)
    attachment.mimetype  # 'application/zip' (3)
    attachment.content_type  # 'application/zip' (4)
    attachment.extension  # 'zip' (5)
    attachment.filename  # 'TMP_PATH' (6)
    attachment.suggested_filename  # 'configuration_MODULETHERMALCYCLING.zip' (7)
    attachment.size  # 226988 (8)
    attachment.size_fmt  # '221.7KiB' (9)

    attachment.save()  # saves to disk (10)
    ```

    1. This is an [itkdb.models.ZipFile][].
    2. The attachment object
    3. The mimetype of the content from the response headers
    4. The mimetype of the content using [itkdb.utils.get_mimetype][]
    5. The extension of the file
    6. The filename of the ephemeral file on disk
    7. The filename extracted from the response headers (may not have one!)
    8. The size of the file in bytes
    9. The human-readable size of the file
    10. If no path is specified, will use `suggested_filename` and save to current working directory.

## Download an attachment from EOS

Downloading an attachment from EOS is less relatively straightforward than from
ITkPD. It requires a two-step process, one to query the component (or test run
or shipment) with the attachment with `noEosToken=False`, and then `GET` the
generated URL for that attachment in the object's attachments. Similar to
[the previous example](#download-an-attachment-from-itkpd), when using
[itkdb.Client][] (and not [itkdb.core.Session][]), the response will
automatically be converted to a [itkdb.models.BinaryFile][]-like object. All
`BinaryFile` have the same baseline set of functionality, with additional
helpers specific to the type of attachment (or file) that has been downloaded
(such as [itkdb.models.ImageFile][] or [itkdb.models.TextFile][]).

In order to reduce the memory overhead, these attachments are ephemeral
(temporarily saved to disk). If you need to persist longer, you can use the
corresponding `attachment.save()` function (see
[itkdb.models.file.BinaryFile.save][]).

=== "Text"

    ```py
    import itkdb

    c = itkdb.Client()

    component = "20UPGFC0083098"

    comp = c.get("getComponent", json={"component": component, "noEosToken": False})
    attachment_info = comp["attachments"][3]
    assert attachment_info["type"] == "eos"  # (1).
    assert attachment_info["title"] == "0x1449a_L2_cold.json"

    attachment = c.get(attachment_info["url"])  # (2).
    attachment  # <itkdb.models.file.TextFile(...) file-like object at TMP_PATH> (3)
    attachment.mimetype  # 'text/plain' (4)
    attachment.content_type  # 'text/plain' (5)
    attachment.extension  # 'txt' (6)
    attachment.filename  # 'TMP_PATH' (7)
    attachment.suggested_filename  # None (8)
    attachment.size  # 1974375 (9)
    attachment.size_fmt  # '1.9MiB' (10)
    attachment.save()  # saves to disk (11)
    ```

    1. Just an assertion to confirm or indicate which attachment we were using for this example (if you wanted to try it out yourself!)
    2. This gives a warning indicating that `itkdb` detected an image-type and will auto-convert: `Changing the mimetype for the response from EOS from 'application/octet-stream' to 'image/jpeg'.`.
    3. The attachment object
    4. The mimetype of the content from the response headers
    5. The mimetype of the content using [itkdb.utils.get_mimetype][]
    6. The extension of the file
    7. The filename of the ephemeral file on disk
    8. The filename extracted from the response headers (may not have one!)
    9. The size of the file in bytes
    10. The human-readable size of the file
    11. If no path is specified, will use `suggested_filename` and save to current working directory. Will not save if `suggested_filename` is `None`

## Upload an attachment

!!! note

    This example uploads an attachment for **components** (`createComponentAttachment`), but you can also do this with **shipments** (`createShipmentAttachment`) and **tests** (`createTestRunAttachment`).

Uploading an attachment to ITkPD or EOS is the same as if you were doing it to
any other API. You can see the documentation from `requests` on how to
[`POST` a multipart-encoded file](https://requests.readthedocs.io/en/latest/user/quickstart/#post-a-multipart-encoded-file).

I recommend that you upload using contexts to automatically close the open file
pointer when done.

=== "ITkPD"

    ```py
    import itkdb

    client = itkdb.Client()

    filename = itkdb.data / "1x1.jpg"  # (1)!

    data = {
        "component": "20UXXAB1234567",
        "title": "a test image attachment",
        "description": "a small image shipped with itkdb",
        "url": filename,
        "type": "file",
    }

    with filename.open("rb") as fpointer:
        files = {"data": itkdb.utils.get_file_components({"data": fpointer})}  # (2)!
        response = client.post("createComponentAttachment", data=data, files=files)  # (3)!

    response["id"]  # '63ff7e7d4069b50036fe0ab9'
    response["code"]  # '756d0ce0213b856b83da494958d2aab4'
    response["awid"]  # 'dcb3f6d1f130482581ba1e7bbe34413c'
    ```

    1. Here, we'll use a small test image that is shipped with `itkdb` for
       demonstration. Feel free to use the same to test your code.
    2. This is typically a tuple specifying the filename, an open pointer to the
       file (readable for streaming the upload), the mimetype, and additional
       headers to set on the request for that specific file. This is specific to how
       `requests` accepts or recognizes the `files` argument here, so refer to their
       documentation. Additionally, [itkdb.utils.get_file_components][] is a
       utility I provide to make this easier to generate (see
       [below](#generating-file-components-for-multipart-uploads) for example
       usage).
    3. While it is called `files` indicating you could upload multiple files, the
       production database only allows uploading a single file.


    The following response keys exist:

    ```py
    [
        "awid",
        "code",
        "contentType",
        "description",
        "filename",
        "id",
        "name",
        "sys",
        "tagList",
        "versionName",
    ]
    ```

=== "EOS"

    ```py
    import itkdb

    client = itkdb.Client(use_eos=True)

    filename = itkdb.data / "1x1.jpg"  # (1)!

    data = {
        "component": "20UXXAB1234567",
        "title": "a test image attachment",
        "description": "a small image shipped with itkdb",
        "url": filename,
        "type": "file",
    }

    with filename.open("rb") as fpointer:
        files = {"data": itkdb.utils.get_file_components({"data": fpointer})}  # (2)!
        response = client.post("createComponentAttachment", data=data, files=files)  # (3)!
        # Ignoring user-specified data={'url': ..., 'type': 'file'} (4)

    response["code"]  # '1c0ee8c12a2f7bd43c3ee997b70ab20c'
    response[
        "url"
    ]  # 'https://eosatlas.cern.ch/eos/atlas/test/itkpd/1/c/0/1c0ee8c12a2f7bd43c3ee997b70ab20c' (5)
    response["token"]  # 'zteos64:...' (6)
    ```

    1. Here, we'll use a small test image that is shipped with `itkdb` for
       demonstration. Feel free to use the same to test your code.
    2. This is typically a tuple specifying the filename, an open pointer to the
       file (readable for streaming the upload), the mimetype, and additional
       headers to set on the request for that specific file. This is specific to how
       `requests` accepts or recognizes the `files` argument here, so refer to their
       documentation. Additionally, [itkdb.utils.get_file_components][] is a
       utility I provide to make this easier to generate (see
       [below](#generating-file-components-for-multipart-uploads) for example
       usage).
    3. This will make two requests, one to the ITkPD API to generate the attachment metadata in the database, and then another request to EOS using the generated metadata from the first request. Additionally, like with ITkPD, EOS only allows uploading a single file.
    4. You will typically see a warning about key/value pairs supplied in the `data` argument that are not being used in the subsequent request to EOS. This is ok, and an indication that the file is in the process of being uploaded to EOS.
    5. The URL on EOS that the file was uploaded to. Notice that it is under three subdirectories named based on the first three characters of the corresponding item mongo [ObjectId](https://www.mongodb.com/docs/manual/reference/method/ObjectId/) for the component, shipment, or test run.
    6.  The ephemeral (short-lived) token associated with the request to upload the file to EOS. Do not save this token as it expires quickly.

    The following response keys exist:

    ```py
    [
        "code",
        "contentType",
        "dateTime",
        "description",
        "filename",
        "filesize",
        "title",
        "token",
        "type",
        "url",
        "userIdentity",
    ]
    ```

## Generating file components for multipart uploads

`requests` has a `files` argument that accepts a couple of different sets of
inputs:

```py
{"data": filepointer}
{"data": (filename, filepointer)}
{"data": (filename, filepointer, filetype)}
{"data": (filename, filepointer, filetype, fileheaders)}
```

But [itkdb.utils.get_file_components][] is a utility function to make it easier
to generate this consistently for you. To use, you can run like so:

```py
import itkdb

with (itkdb.data / "1x1.jpg").open("rb") as image_fp:
    itkdb.utils.get_file_components({"data": image_fp})
    # ('1x1.jpg', <_io.BufferedReader...>, 'image/jpeg', {})

with (itkdb.data / "1x1.sh").open("rb") as text_fp:
    itkdb.utils.get_file_components({"data": ("my-script.sh", text_fp)})
    # ('my-script.sh', <_io.BufferedReader...>, 'text/x-shellscript', {}) (1)

with (itkdb.data / "tiny.root").open("rb") as root_fp:
    itkdb.utils.get_file_components(
        {"data": ("analysis.root", root_fp, "application/x+cern-root")}
    )
    # ('analysis.root', <_io.BufferedReader...>, 'application/x+cern-root', {}) (2)
```

1. The filename is `my-script.sh` rather than `1x1.sh`.
2. There is no official mimetype for ROOT files assigned with
   [IANA](https://www.iana.org/assignments/media-types/media-types.xhtml). If
   you don't set one, the default `application/octet-stream` will be used. This
   default is technically ok as the mimetypes are treated as hints/suggestions,
   rather than as a rule.

## Delete an attachment

!!! note

    This example deletes an attachment for **components** (`deleteComponentAttachment`), but you can also do this with **shipments** (`deleteShipmentAttachment`) and **tests** (`deleteTestRunAttachment`).

!!! note

    Because of the flow for deleting attachments, the attachment type is not known ahead of time so you must have `itkdb[eos]` installed and `use_eos=True` enabled.

Deleting an attachment works as you expect, but `itkdb` will do additional work
to remove the attachment from EOS if it is on EOS. The code below will assume
this attachment exists and show you the code for how to delete it:

```py
import itkdb

client = itkdb.Client(use_eos=True)

component = "20UXXAB1234567"  # (1)!
attachment = "756d0ce0213b856b83da494958d2aab4"  # (2)!

response = client.post(
    "deleteComponentAttachment", json={"component": component, "code": attachment}
)

response["id"]  # '63ff7e7d4069b50036fe0ab9'
response["code"]  # '756d0ce0213b856b83da494958d2aab4'
response["awid"]  # 'dcb3f6d1f130482581ba1e7bbe34413c'
```

1. Here, we use the same component identifier from
   [uploading an attachment](#upload-an-attachment) example.
2. This is the code of the attachment reported from ITkPD, not the mongo
   ObjectID.
3. While it is called `files` indicating you could upload multiple files, the
   production database only allows uploading a single file.

=== "Attachment is stored in ITkPD"

    The following response keys exist:

    ```py
    ["attachment"]
    ```

    and under `attachment` is:

    ```py
    [
        "dateTime",
        "title",
        "description",
        "type",
        "userIdentity",
        "code",
        "contentType",
        "filename",
    ]
    ```

=== "Attachment is stored in EOS"

    The following response keys exist:

    ```py
    ["attachment", "token"]
    ```

    and under `attachment` is:

    ```py
    [
        "dateTime",
        "title",
        "description",
        "type",
        "filesize",
        "userIdentity",
        "code",
        "contentType",
        "filename",
        "url",
    ]
    ```

## Using a bearer token for your requests

`itkdb` supports a [itkdb.typing.UserLike][] object which allows one to change the method of authentication (or create your own `User` type) that is used by [itkdb.Client][]. In this example, we will demonstrate how to switch to [itkdb.core.UserBearer][].

```py
import itkdb

user = itkdb.core.UserBearer(bearer="mybearertoken")  # (1)!
client = itkdb.Client(user=user)  # (2)!
```

1. Create your [itkdb.core.UserBearer][] user.
2. Tell the [itkdb.Client][] to use your user. Then, the `client` will make requests to the API using the configured API url.
