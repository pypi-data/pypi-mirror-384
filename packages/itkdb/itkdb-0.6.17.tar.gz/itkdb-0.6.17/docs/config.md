# Configuration

`itkdb` comes with the ability to configure a few things via either environment
variables or just through python alone. This configuration is done via
[simple-settings][].

---

## Environment Variables

See [itkdb.settings.base][] for all environment variables that can be set. All
environment variables for this package are prefixed with `ITKDB_`. As of now,
there are:

| Variable                   | Default                                                                                  | Description                                                                                                                |
| -------------------------- | ---------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------- |
| ITKDB_ACCESS_CODE1         | `""`                                                                                     | First access code                                                                                                          |
| ITKDB_ACCESS_CODE2         | `""`                                                                                     | Second access code                                                                                                         |
| ITKDB_AUDREYTWO_API_KEY    | `""`                                                                                     | API key for Audrey II                                                                                                      |
| ITKDB_ACCESS_SCOPE         | `"openid https://itkpd-test.unicorncollege.cz"`                                          | OIDC scope for the API                                                                                                     |
| ITKDB_ACCESS_AUDIENCE      | `"https://itkpd-test.unicorncollege.cz"`                                                 | OIDC aucience for the API                                                                                                  |
| ITKDB_AUTH_URL             | `"https://uuidentity.plus4u.net/uu-oidc-maing02/bb977a99f4cc4c37a2afce3fd599d0a7/oidc/"` | OIDC Authentication url for the API                                                                                        |
| ITKDB_API_URL              | `"https://itkpd-test.unicorncollege.cz/"`                                                | Base url for the API                                                                                                       |
| ITKDB_CASSETTE_LIBRARY_DIR | `"tests/integration/cassettes"`                                                          | Local path for storing recorded requests for playback (developer setting)                                                  |
| ITKDB_LEEWAY               | 2                                                                                        | Default amount of time (in seconds) for leeway when checking local machine time against server response for authentication |

!!! note "Added in version 0.4.0"

    - `ITKDB_ACCESS_SCOPE`
    - `ITKDB_ACCESS_AUDIENCE`
    - `ITKDB_LEEWAY`

### Load environment variables from file

`itkdb` also uses [python-dotenv](https://saurabh-kumar.com/python-dotenv/) to
load environment variables from a file called `.env` in the current directory
you're running `itkdb` from. This allows you to dynamically inject environment
variables in while running, but without the need to export in `.bash_profile` or
similar. You can create a `.env` file with contents like

```bash title=".env"
ITKDB_ACCESS_CODE1=abcdef
ITKDB_ACCESS_CODE2=123456
```

Or for access to the reporting backup

```bash title=".env"
ITKDB_AUDREYTWO_API_KEY=mytoken
```
