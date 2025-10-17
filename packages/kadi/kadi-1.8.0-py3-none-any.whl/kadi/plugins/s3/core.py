# Copyright 2024 Karlsruhe Institute of Technology
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
from flask import current_app
from flask import send_file
from s3fs import S3FileSystem
from werkzeug.datastructures import Headers

from kadi.lib.storage.core import BaseStorage
from kadi.lib.web import encode_filename


class S3Storage(BaseStorage):
    """Storage provider that uses an S3-compatible object store.

    :param endpoint_url: The base URL of the object store.
    :param bucket_name: The name of a bucket the storage provider operates in.
    :param access_key: (optional) The access key used for authentication. If not
        provided, the standard configuration locations of the Boto3 client library will
        be checked for this value instead.
    :param secret_key: (optional) The secret key used for authentication. If not
        provided, the standard configuration locations of the Boto3 client library will
        be checked for this value instead.
    :param region_name: (optional) The region name to use when accessing the object
        store. Only relevant for certain object store implementations.
    :param signature_version: (optional) The signature version to use for signing
        requests. Only relevant for certain object store implementations.
    :param use_presigned_urls: (optional) Flag indicating whether presigned URLs should
        be generated when downloading files. This allows direct file downloads via the
        underlying object store, including support for range requests, but requires the
        object store to be reachable externally.
    :param presigned_url_expiration: (optional) The expiration time in seconds to use
        for all generated, presigned URLs. Only relevant if ``use_presigned_urls`` is
        ``True``.
    :param config_kwargs: (optional) A dictionary of additional configuration values
        that will be passed as keyword arguments to the configuration object of the
        Botocore client library.
    """

    def __init__(
        self,
        *,
        endpoint_url,
        bucket_name,
        access_key=None,
        secret_key=None,
        region_name=None,
        signature_version=None,
        use_presigned_urls=True,
        presigned_url_expiration=60,
        config_kwargs=None,
    ):
        super().__init__("s3", storage_name="S3")

        self._endpoint_url = endpoint_url
        self._bucket_name = bucket_name
        self._access_key = access_key
        self._secret_key = secret_key
        self._region_name = region_name
        self._signature_version = signature_version
        self._use_presigned_urls = use_presigned_urls
        self._presigned_url_expiration = presigned_url_expiration
        self._config_kwargs = config_kwargs if config_kwargs is not None else {}
        self._cached_fs = None

    @property
    def _fs(self):
        if self._cached_fs is None:
            # Needs to be instantiated lazily, as the storage provider itself is created
            # during app initialization, which may be followed by forking. However, the
            # S3FileSystem class is not fork-safe due to creating an event loop in a
            # separate thread during instantiation.
            self._cached_fs = S3FileSystem(
                endpoint_url=self._endpoint_url,
                key=self._access_key,
                secret=self._secret_key,
                config_kwargs={
                    "region_name": self._region_name,
                    "signature_version": self._signature_version,
                    **self._config_kwargs,
                },
            )

        return self._cached_fs

    def _create_filepath(self, identifier):
        if not identifier:
            raise ValueError(
                f"Given file identifier '{identifier}' is not suitable for creating a"
                " file path."
            )

        return f"{self._bucket_name}/{identifier}"

    def exists(self, identifier):
        filepath = self._create_filepath(identifier)
        return self._fs.exists(filepath)

    def get_size(self, identifier):
        filepath = self._create_filepath(identifier)
        return self._fs.info(filepath)["size"]

    def get_mimetype(self, identifier):
        file_size = self.get_size(identifier)

        with self.open(identifier) as f:
            return self._get_mimetype(f, file_size)

    def open(self, identifier, mode="rb", encoding=None):
        filepath = self._create_filepath(identifier)
        return self._fs.open(filepath, mode=mode, encoding=encoding)

    def save(self, identifier, stream, max_size=None):
        with self.open(identifier, mode="wb") as f:
            return self._save(f, stream, max_size=max_size, calculate_checksum=True)

    def move(self, src_identifier, dst_identifier):
        src_filepath = self._create_filepath(src_identifier)
        dst_filepath = self._create_filepath(dst_identifier)
        self._fs.mv(src_filepath, dst_filepath)

    def delete(self, identifier):
        filepath = self._create_filepath(identifier)
        self._fs.rm(filepath)

    def merge(self, identifier, identifier_list):
        filepath = self._create_filepath(identifier)
        chunkpaths = [
            self._create_filepath(chunk_identifier)
            for chunk_identifier in identifier_list
        ]
        self._fs.merge(filepath, chunkpaths)

    def download(self, identifier, *, filename, mimetype, as_attachment=True):
        filepath = self._create_filepath(identifier)

        if not self._use_presigned_urls:
            info = self._fs.info(filepath)

            # Remove the double quotes of the returned ETag.
            etag = info["ETag"][1:-1]
            last_modified = info["LastModified"]

            return send_file(
                self.open(identifier),
                download_name=filename,
                mimetype=mimetype,
                as_attachment=as_attachment,
                etag=etag,
                last_modified=last_modified,
            )

        headers = Headers()
        headers.set(
            "Content-Disposition",
            "attachment" if as_attachment else "inline",
            **encode_filename(filename),
        )

        presigned_url = self._fs.url(
            filepath,
            expires=self._presigned_url_expiration,
            ResponseContentType=mimetype,
            ResponseContentDisposition=headers.get("Content-Disposition"),
        )
        headers.set("Location", presigned_url)

        return current_app.response_class(
            response=presigned_url,
            status=302,
            mimetype=mimetype,
            headers=headers,
            direct_passthrough=True,
        )
