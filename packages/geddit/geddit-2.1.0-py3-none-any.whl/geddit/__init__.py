import logging
import os
import urllib.parse
from urllib.request import urlopen

import requests
from google.cloud import secretmanager_v1, storage

LOG = logging.getLogger(__name__)


def geddit(url):
    """
    Fetch the content of a resource at a given URL and return the fetched content as a bytes
    object.

    The following schemes are supported:

    * file: fetch from a file on the local file system. (Default if no scheme is provided.)
    * https: fetch using HTTP over TLS. HTTP basic authentication is not supported since it
        involves having the cleartext password in the URL.
    * gs: fetch from a Google Cloud Storage object. The URL should have the form
        "gs://bucket/path/to/object".
    * sm: fetch from a Google Secret Manager secret. The URL should have the form
        "sm://project/secret[#version]". If no version is provided the "latest" version is used.
    * data: parse RFC 2397 "data URLs"

    For "gs" and "sm" URLs, application default credentials are used.

    Raises ValueError if the URL has an unknown scheme. Fetch errors of other kinds are raised
    using appropriate exceptions for the backend specific to the scheme.

    """
    components = urllib.parse.urlsplit(url, scheme="file")
    fetch_cb = _SCHEME_MAP.get(components.scheme)
    if fetch_cb is None:
        raise ValueError(f'Unknown URL scheme "{components.scheme}" for URL "{url}"')
    return fetch_cb(components)


def _fetch_file_url(components):
    """
    Fetch the contents of a local file given the split file:// URL components.

    """
    if not os.path.isabs(components.path):
        raise ValueError("file:// URL path must be absolute")
    with open(components.path, "rb") as fobj:
        return fobj.read()


def _fetch_https_url(components):
    """
    Fetch a HTTP over TLS URL which has been parsed into components.

    """
    response = requests.get(urllib.parse.urlunsplit(components[:5]))
    response.raise_for_status()
    return response.content


def _fetch_secret_manager_url(components):
    """
    Fetch a secret manager URL which has been parsed into components.

    """
    project_id = components.netloc
    secret_name = components.path.lstrip("/")
    version = components.fragment if components.fragment != "" else "latest"

    # Sanity check that there aren't any path components in the secret name or version.
    if "/" in secret_name or "/" in version:
        raise ValueError("Secret Manager URL must have form sm://PROJECT_ID/SECRET#VERSION")

    client = secretmanager_v1.SecretManagerServiceClient()
    secret_path = client.secret_version_path(project_id, secret_name, version)
    return client.access_secret_version(name=secret_path).payload.data


def _fetch_storage_url(components):
    """
    Fetch a Cloud storage URL which has been parsed into components.

    """
    bucket = components.netloc
    blob_path = components.path.lstrip("/")
    generation = components.fragment if components.fragment != "" else None

    client = storage.Client()
    # using bucket() over get_bucket() to remove the need for bucket permissions
    bucket = client.bucket(bucket)
    blob = bucket.get_blob(blob_path, generation=generation)

    return blob.download_as_bytes()


def _fetch_data_url(components):
    """
    Fetch a data URL which has been parsed into components.

    """
    # Top tip: urlopen() has supported data URLs since Python 3.4
    with urlopen(urllib.parse.urlunsplit(components[:5])) as response:
        return response.read()


# A table mapping URL schemes into the corresponding callable for that scheme.
_SCHEME_MAP = {
    "file": _fetch_file_url,
    "gs": _fetch_storage_url,
    "https": _fetch_https_url,
    "sm": _fetch_secret_manager_url,
    "data": _fetch_data_url,
}
