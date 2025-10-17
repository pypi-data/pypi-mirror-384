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
import csv
import tarfile
import zipfile
from base64 import b64encode
from io import BytesIO

import h5py
import numpy as np
from charset_normalizer import from_bytes
from flask import current_app
from flask import json
from PIL import Image

import kadi.lib.constants as const
from kadi.lib.plugins.core import run_hook
from kadi.lib.web import url_for


# Prefix of the (OpenXML based) MS office MIME types.
MS_OFFICE_PREFIX = "application/vnd.openxmlformats-officedocument"

# MIME types that currently should not be previewed at all, rather than showing an
# unexpected preview.
IGNORED_MIMETYPES = [
    f"{MS_OFFICE_PREFIX}.wordprocessingml.document",
    f"{MS_OFFICE_PREFIX}.presentationml.presentation",
]

ARCHIVE_MIMETYPES = [
    const.MIMETYPE_ZIP,
    "application/gzip",
    "application/x-bzip2",
    "application/x-tar",
]
AUDIO_MIMETYPES = [
    "audio/flac",
    "audio/mpeg",
    "audio/ogg",
    "audio/wav",
    "audio/x-wav",
]
HDF_MIMETYPES = [
    "application/x-hdf",
    "application/x-hdf5",
    # Matlab application data may be based on HDF5.
    "application/x-matlab-data",
    "application/matlab-mat",
]
IMAGE_MIMETYPES = [
    "image/bmp",
    "image/gif",
    "image/tiff",
    "image/x-bmp",
    "image/x-ms-bmp",
]
OBJ_MIMETYPE = "model/obj"
STL_MIMETYPES = [
    "application/sla",
    "model/stl",
    "model/x.stl-ascii",
    "model/x.stl-binary",
]
VTP_MIMETYPES = [
    const.MIMETYPE_BINARY,
    const.MIMETYPE_XML,
]
XYZ_MIMETYPE = "chemical/x-xyz"

# Maximum amount of entries for archive-like previews.
MAX_ARCHIVE_ENTRIES = 500
# Maximum amount of rows for CSV previews.
MAX_CSV_ROWS = 500
# Maximum amount of chars to read for text-based previews.
MAX_TEXT_CHARS = 100_000
# Maximum width/height for image thumbnails.
MAX_THUMBNAIL_RESOLUTION = 1_024


def get_builtin_preview_data(file):
    """Get the preview data of a file based on all built-in preview types.

    :param file: The :class:`.File` to get the preview data of.
    :return: The preview type and preview data as tuple or `None`` if none of the
        built-in preview types are suitable.
    """
    if file.mimetype in IGNORED_MIMETYPES:
        return None

    is_text_based = file.magic_mimetype.startswith("text/")
    download_url = url_for(
        "api.download_file", record_id=file.record_id, file_id=file.id
    )

    # Archive preview, which consists of a hierarchical list of entries and metadata.
    if file.magic_mimetype in ARCHIVE_MIMETYPES:
        archive_data = _get_archive_preview(file)

        if archive_data is not None:
            return "archive", archive_data

    # Audio preview, which just returns the download link of the file.
    if file.magic_mimetype in AUDIO_MIMETYPES:
        return "audio", download_url

    # CSV preview, which consists of tabular text data as well as some additional
    # metadata (encoding and whether a header is detected).
    if file.magic_mimetype == const.MIMETYPE_CSV or (
        is_text_based and file.mimetype == const.MIMETYPE_CSV
    ):
        text_data = _get_text_data(file)

        if text_data is not None:
            csv_data = _get_csv_preview(text_data["data"], text_data["encoding"])

            if csv_data is not None:
                return "csv", csv_data

    # Excel preview, which just returns the download link of the file.
    if file.magic_mimetype == f"{MS_OFFICE_PREFIX}.spreadsheetml.sheet":
        return "excel", download_url

    # HDF5 preview, which consists of a hierarchical list of entries and metadata.
    if file.magic_mimetype in HDF_MIMETYPES:
        hdf_data = _get_hdf_preview(file)

        if hdf_data is not None:
            return "hdf", hdf_data

    # Image preview for image types that can be previewed directly, in which case the
    # direct preview link of the file is returned.
    if file.magic_mimetype in const.IMAGE_MIMETYPES:
        return "image", url_for(
            "api.preview_file", record_id=file.record_id, file_id=file.id
        )

    # Image preview for image types that cannot be previewed directly. These images are
    # converted to a base64 encoded PNG thumbnail.
    if file.magic_mimetype in IMAGE_MIMETYPES:
        image_data = _get_image_preview(file)

        if image_data is not None:
            return "image", image_data

    # JSON preview, which consists of the parsed JSON content of the file.
    if file.magic_mimetype in {const.MIMETYPE_JSON, const.MIMETYPE_DASHBOARD}:
        json_data = _get_json_preview(file)

        if json_data is not None:
            return "json", json_data

    # Markdown preview, which consists of lines of text and the corresponding encoding.
    if file.magic_mimetype == const.MIMETYPE_MD or (
        is_text_based and file.mimetype == const.MIMETYPE_MD
    ):
        text_data = _get_text_data(file)

        if text_data is not None:
            return "markdown", _get_text_preview(
                text_data["data"], text_data["encoding"]
            )

    # OBJ preview, which just returns the download link of the file.
    if file.magic_mimetype == OBJ_MIMETYPE or (
        is_text_based and file.mimetype == OBJ_MIMETYPE
    ):
        return "obj", download_url

    # PDF preview, which just returns the direct preview link of the file.
    if file.magic_mimetype == const.MIMETYPE_PDF:
        return "pdf", url_for(
            "api.preview_file", record_id=file.record_id, file_id=file.id
        )

    # STL preview, which just returns the download link of the file.
    if file.magic_mimetype in STL_MIMETYPES or (
        (is_text_based or file.magic_mimetype == const.MIMETYPE_BINARY)
        and file.mimetype in STL_MIMETYPES
    ):
        return "stl", download_url

    # Video preview, which just returns the download link of the file.
    if file.magic_mimetype == "video/mp4":
        return "video", download_url

    # VTP preview, which just returns the download link of the file. As there are no
    # standardized MIME types, we have to partially rely on the file name.
    if file.magic_mimetype in VTP_MIMETYPES and file.name.endswith(".vtp"):
        return "vtp", download_url

    # Workflow preview, which just returns the download link of the file.
    if file.magic_mimetype == const.MIMETYPE_FLOW:
        return "workflow", download_url

    # XYZ preview, which just returns the download link of the file.
    if file.magic_mimetype == XYZ_MIMETYPE or (
        is_text_based and file.mimetype == XYZ_MIMETYPE
    ):
        return "xyz", download_url

    return None


def get_preview_data(file, use_fallback=True):
    """Get the preview data of a file.

    Uses the :func:`kadi.plugins.spec.kadi_get_preview_data` plugin hook for custom
    preview data.

    :param file: The :class:`.File` to get the preview data of.
    :param use_fallback: (optional) Flag indicating whether the file should be checked
        for textual data as fallback.
    :return: The preview type and preview data as tuple, which are always guaranteed to
        be JSON serializable. If either the preview type or data could not be
        determined, ``None`` is returned.
    """
    if file.size == 0:
        return None

    try:
        preview_data = run_hook("kadi_get_preview_data", file=file)
    except Exception as e:
        current_app.logger.exception(e)
        return None

    if preview_data is not None:
        if (
            not isinstance(preview_data, tuple)
            or not len(preview_data) == 2
            or None in preview_data
        ):
            current_app.logger.error(f"Invalid preview data format for {file!r}.")
            return None

        try:
            # Check whether the data is JSON serializable.
            json.dumps(preview_data, sort_keys=False)
        except Exception as e:
            current_app.logger.exception(e)
            return None

    if preview_data is None and use_fallback:
        text_data = _get_text_data(file)

        if text_data is not None:
            return "text", _get_text_preview(text_data["data"], text_data["encoding"])

    return preview_data


def _archive_entries_to_list(entries):
    results = []

    for name, entry in entries.items():
        item = {"name": name, **entry}

        if entry["is_dir"]:
            item["children"] = _archive_entries_to_list(item["children"])

        results.append(item)

    return sorted(results, key=lambda item: (not item["is_dir"], item["name"]))


def _get_archive_preview(file):
    infolist = []

    if file.magic_mimetype == const.MIMETYPE_ZIP:
        try:
            with file.storage.open(file.identifier) as f:
                with zipfile.ZipFile(f) as zip_file:
                    infolist = zip_file.infolist()[:MAX_ARCHIVE_ENTRIES]

        except zipfile.BadZipFile:
            return None
    else:
        # Tar files do not have a central file list, so we limit the preview to
        # smaller files.
        if file.size > const.PREVIEW_MAX_SIZE:
            return None

        try:
            with file.storage.open(file.identifier) as f:
                with tarfile.open(fileobj=f) as tar_file:
                    num_items = 0

                    for item in tar_file:
                        infolist.append(item)
                        num_items += 1

                        if num_items >= MAX_ARCHIVE_ENTRIES:
                            break

        except tarfile.TarError:
            return None

    entries = {}

    for item in infolist:
        if isinstance(item, zipfile.ZipInfo):
            is_dir = item.filename.endswith("/")
            size = item.file_size
            parts = item.filename.split("/")

            if not is_dir:
                name = parts[-1]
                parents = parts[:-1]
            else:
                name = parts[-2]
                parents = parts[:-2]

        else:
            is_dir = item.isdir()
            size = item.size
            parts = item.name.split("/")
            name = parts[-1]
            parents = parts[:-1]

        current_dir = entries

        for parent in parents:
            if parent not in current_dir:
                # Depending on how the archive was created, not all directories might be
                # listed separately.
                current_dir[parent] = {"is_dir": True, "children": {}}

            current_dir = current_dir[parent]["children"]

        # Depending on how the archive was created, some entries might be listed
        # multiple times.
        if name in current_dir:
            continue

        current_dir[name] = {"is_dir": is_dir}

        if not is_dir:
            current_dir[name]["size"] = size
        else:
            current_dir[name]["children"] = {}

    return _archive_entries_to_list(entries)


def _get_file_encoding(file):
    with file.storage.open(file.identifier) as f:
        # Note that larger files might produce incorrect results for multibyte encodings
        # when reading them only partially.
        results = from_bytes(f.read(10 * const.ONE_MB))

    best_result = results.best()

    if best_result:
        return best_result.encoding

    return None


def _get_text_data(file):
    encoding = _get_file_encoding(file)

    if encoding is None:
        return None

    try:
        with file.storage.open(file.identifier, mode="r", encoding=encoding) as f:
            return {
                "data": f.read(MAX_TEXT_CHARS),
                "encoding": encoding,
            }
    except:
        return None


def _get_csv_preview(data, encoding):
    rows = []
    sniffer = csv.Sniffer()

    try:
        dialect = sniffer.sniff(data)
        has_header = sniffer.has_header(data)

        for row in csv.reader(data.splitlines(), dialect=dialect):
            # Ignore completely empty rows.
            if len(row) > 0:
                rows.append(row)

            if len(rows) >= MAX_CSV_ROWS:
                break

    except Exception as e:
        current_app.logger.debug(e, exc_info=True)
        return None

    return {
        "rows": rows,
        "encoding": encoding,
        "has_header": has_header,
    }


def _convert_hdf_attr(attr):
    if isinstance(attr, np.ndarray):
        attrs = []

        for _attr in attr:
            attrs.append(_convert_hdf_attr(_attr))

        return attrs

    try:
        attr = attr.item()

        if isinstance(attr, bytes):
            attr = attr.decode()

        return attr
    except:
        return str(attr)


def _get_hdf_entries(h5_file, entry_count=0):
    entry = {
        "name": h5_file.name.split("/")[-1] or "/",
        "is_group": False,
        "attrs": {},
    }

    # Record the total amount of entries, taking into account the recursion.
    entry_count += 1

    for key, value in h5_file.attrs.items():
        entry["attrs"][key] = _convert_hdf_attr(value)

    if isinstance(h5_file, h5py.Group):
        entry["is_group"] = True
        entry["children"] = []

        for value in h5_file.values():
            if entry_count >= MAX_ARCHIVE_ENTRIES:
                break

            new_entry, entry_count = _get_hdf_entries(value, entry_count=entry_count)
            entry["children"].append(new_entry)
    else:
        entry["meta"] = {}

        for attr in ["dtype", "ndim", "shape", "maxshape", "size", "nbytes"]:
            entry["meta"][attr] = str(getattr(h5_file, attr, ""))

    return entry, entry_count


def _get_hdf_preview(file):
    with file.storage.open(file.identifier) as f:
        try:
            h5_file = h5py.File(f)
            hdf_data = _get_hdf_entries(h5_file)[0]
            return [hdf_data]
        except Exception as e:
            current_app.logger.debug(e, exc_info=True)
            return None


def _get_image_preview(file):
    if file.size > const.PREVIEW_MAX_SIZE:
        return None

    image_data = BytesIO()

    with file.storage.open(file.identifier) as f:
        try:
            with Image.open(f) as image:
                # Special handling to support 16 bit TIFF images.
                if image.format == "TIFF" and image.mode == "I;16":
                    image = image.point(lambda i: i * (1 / 256)).convert("L")

                image.thumbnail((MAX_THUMBNAIL_RESOLUTION, MAX_THUMBNAIL_RESOLUTION))
                image.save(image_data, format="PNG")

            image_data = b64encode(image_data.getvalue()).decode()

        except Exception as e:
            current_app.logger.debug(e, exc_info=True)
            return None

    return f"data:image/png;base64,{image_data}"


def _get_json_preview(file):
    if file.size > const.PREVIEW_MAX_SIZE:
        return None

    encoding = _get_file_encoding(file)

    if encoding is None:
        return None

    try:
        with file.storage.open(file.identifier, mode="r", encoding=encoding) as f:
            return {
                "json": json.load(f),
                "encoding": encoding,
            }
    except Exception as e:
        current_app.logger.debug(e, exc_info=True)
        return None


def _get_text_preview(data, encoding):
    return {
        "lines": data.rstrip().splitlines(),
        "encoding": encoding,
    }
