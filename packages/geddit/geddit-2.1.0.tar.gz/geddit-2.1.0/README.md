# Geddit

Simple zero-configuration retrieval of resources by URL.

This module provides a single `geddit` function which takes a single parameter
specifying the URL to fetch. It will return a `bytes` object with the contents
of the resource at that URL or will raise an exception specific to the URL
scheme.

This library is intended to be used in situations where scheme-specific
configuration can be inferred from the environment. (For example, in Google
Cloud-hosted environments there is usually a default identity which the services
run as. This identity will be used to fetch resources specified via the `gs` or
`sm` schemes.)

This library is *not* intended to replace general use libraries such as
`requests`.

## Examples

```python
from geddit import geddit

# The default scheme is file://
geddit('file:///etc/issue')     # == b'Debian GNU/Linux 10 \\n \\l\n\n'
geddit('/etc/issue')            # == b'Debian GNU/Linux 10 \\n \\l\n\n'
geddit('./README.md')           # Raises: ValueError

# Fetching using HTTP over TLS
geddit('https://www.gov.uk/bank-holidays.json')[:20]  # == b'{"england-and-wales"'

# HTTP errors are reported
geddit('https://www.example.com/not-found')  # raises requests.exceptions.HTTPError

# Google Storage objects. Uses default application credentials.
geddit('gs://my-bucket/some-object')          # fetches latest generation
geddit('gs://my-bucket/some-object#abcdefg')  # fetches generation abcdefg

# Google Secret Manager secrets. Uses default application credentials.
geddit('sm://my-project/some-secret')       # fetches latest version
geddit('sm://my-project/some-secret#3')     # fetches version 3

# Data URLs.
geddit('data:application/x-yaml;charset=utf-8;base64,eyJmb28iOjF9')  # == b'{"foo":1}'
```

## Requirements

* Python >= 3.9.

## Installation

The [latest release of this library on PyPI](https://pypi.org/project/geddit/)
can be installed using `pip`:

```bash
$ pip3 install geddit
```

The library can also be installed directly from the git repository if you want
the most up-to-date version.
```bash
$ pip3 install git+https://gitlab.developers.cam.ac.uk/uis/devops/lib/geddit.git
```

For developers, the tool can be installed from a cloned repo using pip:
```bash
$ cd /path/to/this/repo
$ pip3 install -e .
```

## Publishing a new release

See the [guidebook section on publishing to
PyPI](https://guidebook.devops.uis.cam.ac.uk/en/latest/workflow/pypi/) for more
information.

## License

This software is licensed under an MIT-like software license. See the [LICENSE
file](LICENSE) for the full text of the license.

## Scheme-specific notes

### file

The `file` scheme is the default scheme. Only absolute paths can be specified.

### https

There is no support for HTTP basic authentication as that involves putting the
cleartext password into the URL.

Non-TLS ("http") URLs are *not* supported.

### gs and sm

Only default application credentials are supported. To use specific credentials,
set the `GOOGLE_APPLICATION_CREDENTIALS` environment variable to the absolute
path to some JSON-formatted credentials.

### data

Data URLs are _not_ good way of passing secrets since their values are
transparent. They can be useful for transferring non-secret configuration or for
use in development environments.
