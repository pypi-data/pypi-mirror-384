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
from mimetypes import guess_type

from sqlalchemy.exc import IntegrityError

import kadi.lib.constants as const
from kadi.ext.db import db
from kadi.lib.db import acquire_lock
from kadi.lib.db import update_object
from kadi.lib.resources.core import signal_resource_change
from kadi.lib.revisions.core import create_revision
from kadi.lib.security import hash_value

from .files import get_custom_mimetype
from .models import Chunk
from .models import ChunkState
from .models import File
from .models import FileState
from .models import UploadState


def delete_upload(upload):
    """Delete an existing upload.

    This will mark the upload for deletion, i.e. only the upload's state will be
    changed.

    :param upload: The upload to delete.
    """
    upload.state = UploadState.INACTIVE


def remove_upload(upload):
    """Remove an upload from storage and from the database.

    Note that this function issues one or more database commits.

    :param upload: The upload to remove.
    """
    delete_upload(upload)
    db.session.commit()

    # Remove any chunks related to the upload as well.
    for chunk in upload.chunks:
        upload.storage.delete(chunk.identifier)
        db.session.delete(chunk)

    upload.storage.delete(upload.identifier)
    db.session.delete(upload)

    db.session.commit()


def save_chunk_data(upload, stream, *, index, size, checksum=None):
    """Save the uploaded chunk data of a chunked upload.

    Note that this function issues one or more database commits.

    :param upload: The upload.
    :param stream: The chunk data as a readable binary stream.
    :param index: The index of the chunk.
    :param size: The size of the chunk in bytes.
    :param checksum: (optional) The checksum of the chunk. If provided, it will be used
        to verify the calculated checksum after saving the chunk.
    :return: The created or updated :class:`.Chunk` object.
    :raises KadiFilesizeExceededError: If the chunk data exceeds the size of its upload
        or the maximum chunk size.
    :raises KadiFilesizeMismatchError: If the actual size of the chunk data does not
        match the provided size.
    :raises KadiChecksumMismatchError: If the actual checksum of the chunk data does not
        match the provided checksum.
    """
    chunk = Chunk.update_or_create(upload=upload, index=index, size=size)
    db.session.commit()

    try:
        chunk.checksum = upload.storage.save(
            chunk.identifier, stream, max_size=min(upload.size, const.UPLOAD_CHUNK_SIZE)
        )

        calculated_size = upload.storage.get_size(chunk.identifier)
        upload.storage.validate_size(calculated_size, chunk.size)

        if checksum is not None:
            upload.storage.validate_checksum(chunk.checksum, checksum)

        chunk.state = ChunkState.ACTIVE

    except:
        chunk.state = ChunkState.INACTIVE
        raise

    finally:
        # Always update the upload's timestamp, since it is relevant for its expiration.
        upload.update_timestamp()
        db.session.commit()

    return chunk


def merge_chunk_data(upload):
    """Merge the chunk data of a chunked upload.

    Note that this function issues one or more database commits or rollbacks.

    :param upload: The upload.
    :return: The newly created or updated file or ``None`` if a conflict occured while
        completing the upload.
    :raises KadiFilesizeMismatchError: If the actual final size of the upload data does
        not match the size provided when the upload was created.
    """
    chunk_identifiers = []
    chunk_checksums = ""

    for chunk in upload.active_chunks.order_by(Chunk.index):
        chunk_identifiers.append(chunk.identifier)
        chunk_checksums += chunk.checksum or ""

    try:
        combined_checksum = hash_value(bytes.fromhex(chunk_checksums), alg="md5")
        upload.checksum = f"{combined_checksum}-{upload.chunk_count}"
    except ValueError:
        pass

    try:
        upload.storage.merge(upload.identifier, chunk_identifiers)

        calculated_size = upload.storage.get_size(upload.identifier)
        upload.storage.validate_size(calculated_size, upload.size)

    except:
        delete_upload(upload)
        raise

    finally:
        db.session.commit()

    return _complete_file_upload(upload)


def save_upload_data(upload, stream, checksum=None):
    """Save the uploaded data of a direct upload.

    Note that this function issues one or more database commits or rollbacks.

    :param upload: The upload.
    :param stream: The upload data as a readable binary stream.
    :param checksum: (optional) The checksum of the upload. If provided, it will be used
        to verify the calculated checksum after saving the upload.
    :return: The newly created or updated file or ``None`` if a conflict occured while
        completing the upload.
    :raises KadiFilesizeExceededError: If the upload data exceeds the size of its upload
        or the maximum direct upload size.
    :raises KadiFilesizeMismatchError: If the actual size of the upload data does not
        match match the size provided when the upload was created.
    :raises KadiChecksumMismatchError: If the actual checksum of the upload data does
        not match the provided checksum.
    """
    try:
        upload.checksum = upload.storage.save(
            upload.identifier,
            stream,
            max_size=min(upload.size, const.UPLOAD_CHUNKED_BOUNDARY),
        )

        calculated_size = upload.storage.get_size(upload.identifier)
        upload.storage.validate_size(calculated_size, upload.size)

        if checksum is not None:
            upload.storage.validate_checksum(upload.checksum, checksum)

    except:
        delete_upload(upload)
        raise

    finally:
        db.session.commit()

    return _complete_file_upload(upload)


def _complete_file_upload(upload):
    if upload.file is None:
        file = File.create(
            creator=upload.creator,
            record=upload.record,
            name=upload.name,
            size=upload.size,
            checksum=upload.checksum,
            storage_type=upload.storage_type,
        )
        db.session.commit()
    else:
        # Lock the file to make sure replacing the metadata and actual file data happens
        # in a single transaction.
        file = acquire_lock(upload.file)

        # Check if the file still exists and is active at this point.
        if file is None or file.state != FileState.ACTIVE:
            delete_upload(upload)
            # Releases the file lock as well.
            db.session.commit()
            return None

        update_object(file, size=upload.size, checksum=upload.checksum)

    if upload.description is not None:
        file.description = upload.description

    try:
        # When replacing a file with a different storage type we have to delete any
        # previous data before updating the storage type.
        if file.storage_type != upload.storage_type:
            file.storage.delete(file.identifier)
            file.storage_type = upload.storage_type

        upload.storage.move(upload.identifier, file.identifier)

        # Determine the magic MIME type, and possibly a custom MIME type, based on the
        # file's content.
        base_mimetype = file.storage.get_mimetype(file.identifier)
        custom_mimetype = get_custom_mimetype(file, base_mimetype=base_mimetype)
        magic_mimetype = base_mimetype if custom_mimetype is None else custom_mimetype

        # Determine the regular MIME type. If no MIME type was given explicitly for the
        # upload, the custom MIME type is taken, if applicable. Otherwise, try to guess
        # the regular MIME type from the filename and fall back to the magic MIME type.
        mimetype = upload.mimetype

        if mimetype is None:
            if custom_mimetype is not None:
                mimetype = custom_mimetype
            else:
                mimetype = guess_type(file.name)[0] or magic_mimetype

        update_object(
            file,
            mimetype=mimetype,
            magic_mimetype=magic_mimetype,
            state=FileState.ACTIVE,
        )
        delete_upload(upload)

        if db.session.is_modified(file):
            file.record.update_timestamp()

        revision = create_revision(file, user=upload.creator)

        # Releases the file lock as well.
        db.session.commit()

    except Exception as e:
        db.session.rollback()

        # If something went wrong at this point when replacing a file, the existing file
        # data has most likely already been deleted or overwritten, so we have to delete
        # the file.
        if upload.file is not None:
            from .files import delete_file

            delete_file(upload.file, user=upload.creator)

        delete_upload(upload)
        db.session.commit()

        if isinstance(e, IntegrityError):
            return None

        raise

    signal_resource_change(revision)

    return file
