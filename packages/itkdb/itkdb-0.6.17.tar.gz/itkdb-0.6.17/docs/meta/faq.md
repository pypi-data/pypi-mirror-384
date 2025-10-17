# FAQ

---

## Requests

**_Q_**: I'm getting an SSL Error when making a request to url containing
`cern.ch`.

**_A_**: If you run into SSL errors with CERN websites, you might need the CERN
certificate chain to sign the certificates correctly. Just add a `verify`
keyword into your calls:

```py
client.get(..., verify=itkdb.data / "CERN_chain.pem")
```

and it should work.

**_Q_**: How do I upload a file to EOS?

**_A_**: To upload a file to EOS, you need to install this package with the
[`eos` feature](../install.md). Then refer to some [examples](../examples.md)
for usage.

**_Q_**: I got a `The token is not yet valid (nbf)` error when trying to
authenticate. How do I fix this?

**_A_**: If you receive an error like so

```
Traceback (most recent call last):
...
jose.exceptions.JWTClaimsError: The token is not yet valid (nbf)
```

then the indication here is that the machine running the code has a clock that
is not properly synced to the timeserver. You will need to figure out how to
re-sync your clock as it is a security issue.

**_Q_**: I got an `ImportError` related to `pycurl` and `libcurl`. How do I fix
this?

**_A_**: If you try running `itkdb` and run into an issue like:

```
Traceback (most recent call last):
...
ImportError: pycurl: libcurl link-time ssl backends (secure-transport, openssl) do not include compile-time ssl backend (none/other)
```

You will need to reinstall pycurl and force re-compilation. This can be done by
first checking the config for `curl` on your machine:

```shell hl_lines="12"
$ curl-config --features
AsynchDNS
GSS-API
HTTPS-proxy
IPv6
Kerberos
Largefile
MultiSSL
NTLM
NTLM_WB
SPNEGO
SSL
UnixSockets
alt-svc
libz
```

and then setting the appropriate compile flags. For example, the above shows I
have `SSL` enabled, if I have `openssl` then...

=== "Mac OSX"

    ``` bash
    $ brew info openssl
    ...
    ...

    For compilers to find openssl@3 you may need to set:
      export LDFLAGS="-L/usr/local/opt/openssl@3/lib"
      export CPPFLAGS="-I/usr/local/opt/openssl@3/include"

    ...
    ```

    which tells me to export the above lines and then I can reinstall correctly:

    ``` bash
    $ export LDFLAGS="-L/usr/local/opt/openssl@3/lib"
    $ export CPPFLAGS="-I/usr/local/opt/openssl@3/include"
    $ python -m pip install --no-cache-dir --compile --ignore-installed --install-option="--with-openssl" pycurl
    ```

=== "lxplus (CC7)"

    Assuming a virtual environment like

    ``` bash
    $ lsetup "views dev4 latest/x86_64-centos7-gcc11-opt"
    $ python3 -m venv venv
    $ source venv/bin/activate
    ```

    I looked up the locations of the installations on lxplus for you already:

    ``` bash
    $ export LDFLAGS="-L/usr/local/lib/openssl"
    $ export CPPFLAGS="-I/usr/local/include/openssl"
    $ export PKG_CONFIG_PATH=$PKG_CONFIG_PATH:/usr/lib/pkgconfig/
    $ python -m pip install --no-cache-dir --compile --ignore-installed --install-option="--with-nss" pycurl
    ```

=== "SWAN [lxplus (CC7)]"

    Assuming a virtual environment like

    ``` bash
    $ python3 -m venv venv
    $ source venv/bin/activate
    ```

    which came with `python3.9` by default on [swan](https://swan.cern.ch), the
    installation flags needed are:

    ``` bash
    $ export LDFLAGS="-L/usr/lib64/openssl"
    $ export CPPFLAGS="-I/usr/include/openssl"
    $ export PKG_CONFIG_PATH=$PKG_CONFIG_PATH:/usr/lib64/pkgconfig/
    $ python -m pip install --no-cache-dir --compile \
                            --ignore-installed \
                            --install-option="--with-nss" pycurl
    ```

=== "lxplus (EL9)"

    Assuming a virtual environment like

    ``` bash
    $ lsetup "views LCG_105 x86_64-el9-gcc11-opt"
    $ python3 -m venv venv
    $ source venv/bin/activate
    ```

    I looked up the locations of the installations on lxplus for you already:

    ``` bash
    $ export LDFLAGS="-L/usr/local/lib/openssl"
    $ export CPPFLAGS="-I/usr/local/include/openssl"
    $ export PKG_CONFIG_PATH=$PKG_CONFIG_PATH:/usr/lib/pkgconfig/
    $ python -m pip install --no-cache-dir --compile --ignore-installed --install-option="--with-nss" pycurl
    ```

Additional note that if you have `pip >= 23.0`, you will need to modify the
commands above to supply:

```bash
--no-use-pep517 --global-option="--with..."
```

instead of using `--install-option` which is deprecated in favor of
`--global-option`, and disabling the use of PEP517 to allow the use of
`--global-option`. An example command with this is below:

```bash
python -m pip install --no-cache-dir --compile \
                      --ignore-installed --no-use-pep517 \
                      --global-option="--with-openssl" pycurl
```

Also be sure that you have the curl headers installed (e.g. via `libcurl-devel`)
on your machine.

## Developing

**_Q_**: How do I update a cassette for a test to include new requests to the database that I added in as functionality in `itkdb`?

**_A_**: You can do so like below's steps. First you need to generate a temporary authenticated client to use for all other tests, but this cassette won't be committed. Then you can generate the new cassette for the test that is failing. The example below is for `integration/test_tests.py`:

```bash
$ rm tests/integration/cassettes/test_user.test_user_good_login.json
$ rm tests/integration/cassettes/test_tests.test_duplicate_test_run.json
$ pytest tests/integration/test_user.py
$ pytest tests/integration/test_tests.py
$ git add tests/integration/cassettes/test_tests.test_duplicate_test_run.json
$ git commit -m "update cassette for test_duplicate_test_run"
```

**_Q_**: How do I tag a new version x.y.z?

**_A_**: `hatch run tag x.y.z`


## Potpourri

**_Q_**: I'm still stuck and I don't see my question here.

**_A_**: I'm still working on fleshing out the FAQs. Check back soon. In the
meantime, file an [issue][].
