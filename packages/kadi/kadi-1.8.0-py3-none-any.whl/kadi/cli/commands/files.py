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
import os
import shutil
import sys

import click
from flask import current_app

import kadi.lib.constants as const
from kadi.cli.main import kadi
from kadi.cli.utils import check_env
from kadi.cli.utils import echo
from kadi.cli.utils import echo_danger
from kadi.cli.utils import echo_success
from kadi.cli.utils import echo_warning
from kadi.ext.db import db
from kadi.lib.exceptions import KadiFilesizeMismatchError
from kadi.lib.storage.core import get_storage_provider
from kadi.lib.tasks.models import Task
from kadi.lib.tasks.models import TaskState
from kadi.modules.records.files import remove_file
from kadi.modules.records.models import File
from kadi.modules.records.models import FileState
from kadi.modules.records.models import Upload
from kadi.modules.records.models import UploadState
from kadi.modules.records.models import UploadType
from kadi.modules.records.uploads import remove_upload


@kadi.group()
def files():
    """Utility commands for file management."""


@files.command()
def check():
    """Check all files stored in the database for inconsistencies.

    Should only be run while the application and Celery are not running.
    """
    num_inconsistencies = 0
    inconsistent_items = []

    # Check all files.
    files_query = File.query.with_entities(
        File.id, File.size, File.storage_type, File.state
    )
    echo(f"Checking {files_query.count()} files...")

    for file in files_query.order_by(File.last_modified.desc()):
        storage = get_storage_provider(file.storage_type)

        # For active files, we check if they exist and if at least their size matches.
        if file.state == FileState.ACTIVE:
            if storage.exists(str(file.id)):
                try:
                    actual_size = storage.get_size(str(file.id))
                    storage.validate_size(actual_size, file.size)

                except KadiFilesizeMismatchError:
                    num_inconsistencies += 1
                    inconsistent_items.append(File.query.get(file.id))

                    echo_danger(
                        f"[{num_inconsistencies}] Mismatched size for active file"
                        f" with storage type '{file.storage_type}' and ID '{file.id}'."
                    )
            else:
                num_inconsistencies += 1
                inconsistent_items.append(File.query.get(file.id))

                echo_danger(
                    f"[{num_inconsistencies}] Found orphaned active file with storage"
                    f" type '{file.storage_type}' and ID '{file.id}'."
                )

        # Inactive files will be handled by the periodic cleanup task eventually.
        elif file.state == FileState.INACTIVE:
            pass

        # Deleted file objects should not have any data associated with them anymore.
        elif file.state == FileState.DELETED and storage.exists(str(file.id)):
            num_inconsistencies += 1
            inconsistent_items.append(File.query.get(file.id))

            echo_danger(
                f"[{num_inconsistencies}] Found deleted file with associated data with"
                f" storage type '{file.storage_type}' and ID '{file.id}'."
            )

    # Check all uploads.
    uploads_query = Upload.query.with_entities(
        Upload.id, Upload.storage_type, Upload.upload_type, Upload.state
    )
    echo(f"Checking {uploads_query.count()} uploads...")

    for upload in uploads_query.order_by(Upload.last_modified.desc()):
        # Active uploads will either be handled once they are finished or by the
        # periodic cleanup task eventually.
        if upload.state == UploadState.ACTIVE:
            pass

        # Inactive uploads will be handled by the periodic cleanup task eventually.
        elif upload.state == UploadState.INACTIVE:
            pass

        elif upload.state == UploadState.PROCESSING:
            # Direct processing uploads should have been handled after the upload was
            # finished or got canceled.
            if upload.upload_type == UploadType.DIRECT:
                num_inconsistencies += 1
                inconsistent_items.append(Upload.query.get(upload.id))

                echo_danger(
                    f"[{num_inconsistencies}] Found processing direct upload with"
                    f" storage type '{upload.storage_type}' and ID '{upload.id}'."
                )
            # For processing chunked uploads, check if the corresponding task is still
            # pending. If no task exists, it may have been canceled forcefully.
            else:
                task = Task.query.filter(
                    Task.name == const.TASK_MERGE_CHUNKS,
                    Task.arguments["args"][0].astext == str(upload.id),
                ).first()

                if task is None or task.state != TaskState.PENDING:
                    num_inconsistencies += 1
                    inconsistent_items.append(Upload.query.get(upload.id))

                    echo_danger(
                        f"[{num_inconsistencies}] Found processing (chunked) upload"
                        f" with storage type '{upload.storage_type}' and ID"
                        f" '{upload.id}' but no pending upload processing task."
                    )

    if num_inconsistencies == 0:
        echo_success("Files checked successfully.")
    else:
        echo_warning(
            f"Found {num_inconsistencies}"
            f" {'inconsistency' if num_inconsistencies == 1 else 'inconsistencies'}."
        )

        if click.confirm(
            "Do you want to resolve all inconsistencies automatically by deleting all"
            " inconsistent database objects and associated data?"
        ):
            for item in inconsistent_items:
                if isinstance(item, File):
                    remove_file(item)
                else:
                    remove_upload(item)

            echo_success("Inconsistencies resolved successfully.")


@files.command()
@click.argument("storage_type")
@click.option("--i-am-sure", is_flag=True)
def migrate(storage_type, i_am_sure):
    """Migrate all file and upload data to a storage provider of the specified type.

    Must only be run while the application and Celery are not running.
    """
    dst_storage = get_storage_provider(storage_type, use_fallback=False)

    if dst_storage is None:
        echo_danger(
            "No storage provider has been configured for storage type"
            f" '{storage_type}'."
        )
        sys.exit(1)

    if not i_am_sure:
        echo_warning(
            "This will migrate all data to the storage provider with storage type"
            f" '{storage_type}'. If you are sure you want to do this, use the flag"
            " --i-am-sure."
        )
        sys.exit(1)

    def _migrate_data(storage_from, storage_to, identifier):
        if storage_from.exists(identifier):
            with storage_from.open(identifier) as f:
                storage_to.save(identifier, f)

    # Migrate all files.
    echo(f"Migrating {File.query.count()} files...")

    for file in File.query.order_by(File.last_modified):
        if file.storage_type == storage_type:
            continue

        src_storage = file.storage
        _migrate_data(src_storage, dst_storage, file.identifier)

        file.storage_type = storage_type
        db.session.commit()

        # Only delete the data in the source storage once the migration of the file data
        # has been completed.
        src_storage.delete(file.identifier)

    # Migrate all uploads.
    echo(f"Migrating {Upload.query.count()} uploads...")

    for upload in Upload.query.order_by(Upload.last_modified):
        if upload.storage_type == storage_type:
            continue

        src_storage = upload.storage
        _migrate_data(src_storage, dst_storage, upload.identifier)

        for chunk in upload.chunks:
            _migrate_data(src_storage, dst_storage, chunk.identifier)

        upload.storage_type = storage_type
        db.session.commit()

        # Only delete the data in the source storage once the migration of the upload
        # and chunk data has been completed.
        src_storage.delete(upload.identifier)

        for chunk in upload.chunks:
            src_storage.delete(chunk.identifier)

    echo_success("Data migrated successfully.")


@files.command()
@click.option("--i-am-sure", is_flag=True)
@check_env
def clean(i_am_sure):
    """Remove all data in the configured local storage and upload paths.

    This command will delete all data stored in the local paths specified via the
    STORAGE_PATH (if configured) and MISC_UPLOADS_PATH configuration values.

    Must only be run while the application and Celery are not running.
    """
    storage_path = current_app.config["STORAGE_PATH"]
    misc_uploads_path = current_app.config["MISC_UPLOADS_PATH"]

    if not i_am_sure:
        msg = "This will remove all data in"

        if storage_path:
            msg += f" '{storage_path}' and '{misc_uploads_path}'."
        else:
            msg += f" '{misc_uploads_path}'."

        msg += " If you are sure you want to do this, use the flag --i-am-sure."

        echo_warning(msg)
        sys.exit(1)

    def _remove_path(path):
        if os.path.isdir(path):
            shutil.rmtree(path)
        else:
            os.remove(path)

    if storage_path:
        for item in os.listdir(storage_path):
            _remove_path(os.path.join(storage_path, item))

    for item in os.listdir(misc_uploads_path):
        _remove_path(os.path.join(misc_uploads_path, item))

    echo_success("Data cleaned successfully.")
