# Copyright 2020 Karlsruhe Institute of Technology
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
import hashlib

import magic
from defusedxml.ElementTree import parse
from flask import current_app
from flask import json

import kadi.lib.constants as const
from kadi.lib.exceptions import KadiChecksumMismatchError
from kadi.lib.exceptions import KadiConfigurationError
from kadi.lib.exceptions import KadiFilesizeExceededError
from kadi.lib.exceptions import KadiFilesizeMismatchError
from kadi.lib.format import filesize


class BaseStorage:
    """Base class for all storage providers.

    Note that storage providers operate on file identifiers, which are used to uniquely
    identify files within the underlying storage system via corresponding, generated
    file paths. All storage methods may raise a :class:`ValueError` if a given file
    identifier is not suitable for generating a file path that the corresponding storage
    can work with. A suitable example of an identifier is a randomly generated UUID or
    variations thereof.

    :param storage_type: The unique type of the storage.
    :param storage_name: (optional) A user-readable name of the storage. Defaults to the
        given storage type.
    """

    def __init__(self, storage_type, storage_name=None):
        self._storage_type = storage_type
        self._storage_name = storage_name if storage_name is not None else storage_type

    @property
    def storage_type(self):
        """Get the type of this storage."""
        return self._storage_type

    @property
    def storage_name(self):
        """Get the name of this storage."""
        return self._storage_name

    @staticmethod
    def _save(
        file, stream, max_size=None, calculate_checksum=False, buffer_size=const.ONE_MB
    ):
        """Save the contents of a binary stream in a file.

        :param file: A writable file-like object operating in binary mode.
        :param stream: The readable binary stream to save.
        :param max_size: (optional) The maximum size that the storage should allow when
            writing to the given file.
        :param calculate_checksum: (optional) Whether an MD5 hash of the stream contents
            should be calculated during the operation.
        :param buffer_size: (optional) The buffer size to use during the operation.
        :return: The calculated checksum if ``calculate_checksum`` is ``True``, ``None``
            otherwise.
        :raises KadiFilesizeExceededError: If the given ``max_size`` was exceeded. Note
            that any contents written to the file until this point will stay intact.
        """
        total_size = 0
        checksum = hashlib.md5() if calculate_checksum else None

        while buf := stream.read(buffer_size):
            total_size += len(buf)

            if max_size is not None and total_size > max_size:
                raise KadiFilesizeExceededError(
                    f"Maximum file size exceeded ({filesize(max_size)})."
                )

            file.write(buf)

            if calculate_checksum:
                checksum.update(buf)

        return checksum.hexdigest() if calculate_checksum else None

    @staticmethod
    def _get_mimetype(file, file_size):
        """Get the MIME type of a file-like object based on its contents.

        :param file: A seekable and readable file-like object operating in binary mode.
        :param file_size: The size of the given file in bytes.
        :return: The MIME type of the file.
        """
        try:
            mimetype = magic.from_buffer(file.read(const.ONE_MB), mime=True)
        except Exception as e:
            current_app.logger.debug(e, exc_info=True)
            return const.MIMETYPE_BINARY

        # Check some common interchangeable MIME types and return the recommended one,
        # if applicable.
        if mimetype == "text/xml":
            return const.MIMETYPE_XML
        if mimetype == "application/csv":
            return const.MIMETYPE_CSV

        # Improve the detection of some common formats for reasonably small files that
        # otherwise may just be detected as plain text.
        if mimetype == const.MIMETYPE_TEXT and file_size <= 10 * const.ONE_MB:
            file.seek(0)

            try:
                json.load(file)
                return const.MIMETYPE_JSON
            except:
                pass

            file.seek(0)

            try:
                parse(file)
                return const.MIMETYPE_XML
            except:
                pass

        return mimetype

    @staticmethod
    def validate_size(actual_size, expected_size):
        """Validate the size of a file using a simple comparison.

        :param actual_size: The actual size of the file.
        :param expected_size: The expected size of the file.
        :raises KadiFilesizeMismatchError: If the sizes don't match.
        """
        if actual_size != expected_size:
            raise KadiFilesizeMismatchError(
                f"File size mismatch (expected: {expected_size}, actual:"
                f" {actual_size})."
            )

    @staticmethod
    def validate_checksum(actual_checksum, expected_checksum):
        """Validate the checksum of a file using a simple comparison.

        :param actual_checksum: The actual checksum of the file.
        :param expected_checksum: The expected checksum of the file.
        :raises KadiChecksumMismatchError: If the checksums don't match.
        """
        if actual_checksum != expected_checksum:
            raise KadiChecksumMismatchError(
                f"File checksum mismatch (expected: {expected_checksum}, actual:"
                f" {actual_checksum})."
            )

    def exists(self, identifier):
        """Check if a file exists.

        :param identifier: The identifier of the file to check.
        :return: ``True`` if the file exists, ``False`` otherwise.
        """
        raise NotImplementedError

    def get_size(self, identifier):
        """Get the size of a file.

        :param identifier: The identifier of the file.
        :return: The size of the file in bytes.
        """
        raise NotImplementedError

    def get_mimetype(self, identifier):
        """Get the MIME type of a file based on its content.

        :param identifier: The identifier of the file.
        :return: The MIME type of the file.
        """
        raise NotImplementedError

    def open(self, identifier, mode="rb", encoding=None):
        """Open a file for reading or writing.

        Note that the file object returned by this method must provide a file-like API
        with the usual IO methods such as ``read``, ``write`` or ``seek``.

        :param identifier: The identifier of the file to open.
        :param mode: (optional) The mode in which the file is opened.
        :param encoding: (optional) The encoding to use when opening the file in text
            mode.
        :return: The opened file object.
        """
        raise NotImplementedError

    def save(self, identifier, stream, max_size=None):
        """Save the contents of a binary stream in a file.

        :param identifier: The identifier of the file.
        :param stream: The readable binary stream to save.
        :param max_size: (optional) The maximum size that the storage should allow for
            the destination file.
        :return: An MD5 hash of the stream contents.
        :raises KadiFilesizeExceededError: If the given ``max_size`` was exceeded. Note
            that any contents written to the file until this point may stay intact.
        """
        raise NotImplementedError

    def move(self, src_identifier, dst_identifier):
        """Move a file to another location.

        :param src_identifier: The identifier of the source file.
        :param dst_identifier: The identifier of the destination file.
        """
        raise NotImplementedError

    def delete(self, identifier):
        """Delete a file if it exists.

        :param identifier: The identifier of the file to delete.
        """
        raise NotImplementedError

    def merge(self, identifier, identifier_list):
        """Create a single file from a list of files.

        :param identifier: The identifier of the destination file.
        :param identifier_list: A list of identifiers of files to merge in sequential
            order. Note that the underlying files will stay intact.
        """
        raise NotImplementedError

    def download(self, identifier, *, filename, mimetype, as_attachment=True):
        """Send a file to a client.

        :param identifier: The identifier of the file to send.
        :param filename: The name of the file to send.
        :param mimetype: The MIME type of the file to send.
        :param as_attachment: (optional) Whether to send the file as an attachment. Note
            that setting this parameter to ``False`` may pose a security risk, depending
            on the file contents, client and context.
        :return: The response object.
        """
        raise NotImplementedError


class NullStorage(BaseStorage):
    """Fallback storage provider used as placeholder for invalid storage types.

    Raises a :class:`.KadiConfigurationError` for all storage provider methods.
    """

    # pylint: disable=abstract-method

    def __init__(self, storage_type):
        super().__init__(storage_type)

    def __getattribute__(self, attr):
        if attr not in {
            "_storage_type",
            "storage_type",
            "_storage_name",
            "storage_name",
        }:
            raise KadiConfigurationError(
                "No storage provider has been configured for storage type"
                f" '{self.storage_type}'."
            )

        return super().__getattribute__(attr)


def get_storage_provider(storage_type, use_fallback=True):
    """Get a configured storage provider for a given storage type.

    :param storage_type: The storage type.
    :param use_fallback: (optional) Whether to return a fallback storage provider if no
        suitable storage provider could be found.
    :return: The storage provider or an instance of :class:`.NullStorage` if no suitable
        storage provider could be found and ``use_fallback`` is ``True``, ``None``
        otherwise.
    """
    storage_provider = current_app.config["STORAGE_PROVIDERS"].get(storage_type)

    if storage_provider is None and use_fallback:
        return NullStorage(storage_type)

    return storage_provider
