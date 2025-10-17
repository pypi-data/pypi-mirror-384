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
from flask import current_app
from PIL import Image

import kadi.lib.constants as const

from .local import LocalStorage


class MiscStorage(LocalStorage):
    """Storage provider used for miscellaneous uploads.

    Uses :class:`.LocalStorage` with a fixed root directory as specified in
    ``MISC_UPLOADS_PATH`` in the application's configuration and a number of only two
    directories for all generated file paths. Note that this provider is not used for
    general record file storage.
    """

    def __init__(self):
        super().__init__(current_app.config["MISC_UPLOADS_PATH"], num_dirs=2)


def save_as_thumbnail(identifier, stream, max_resolution=(512, 512)):
    """Save image data as a JPEG thumbnail.

    Uses the :class:`.MiscStorage` to store the thumbnails.

    :param identifier: A file identifier that will be passed to the storage in order to
        save the image data.
    :param stream: The image data as a readable binary stream. The actual data must be
        of one of the image types defined in :const:`kadi.lib.constants.IMAGE_MIMETYPES`
        and must have a maximum size as defined in
        :const:`kadi.lib.constants.IMAGE_MAX_SIZE`.
    :param max_resolution: (optional) The maximum resolution of the thumbnail in pixels.
    :return: ``True`` if the thumbnail was saved successfully, ``False`` otherwise. Note
        that the original image file may be (partially) saved regardless of whether the
        thumbnail could be generated from it.
    """
    storage = MiscStorage()

    try:
        storage.save(identifier, stream, max_size=const.IMAGE_MAX_SIZE)
        mimetype = storage.get_mimetype(identifier)

        if mimetype not in const.IMAGE_MIMETYPES:
            return False

        with storage.open(identifier) as f:
            with Image.open(f) as image:
                # Convert the image into a uniform mode and create a thumbnail from it.
                image = image.convert("RGBA")
                image.thumbnail(max_resolution)

                # Paste the image contents onto a white background.
                new_image = Image.new("RGB", image.size, color=(255, 255, 255))
                new_image.paste(image, mask=image.getchannel("A"))

        with storage.open(identifier, mode="wb") as f:
            new_image.save(f, format="JPEG", quality=95)

        return True

    except Exception as e:
        current_app.logger.exception(e)

    return False


def delete_thumbnail(identifier):
    """Delete a thumbnail.

    This is the inverse operation of :func:`save_as_thumbnail`.

    :param identifier: See :func:`save_as_thumbnail`.
    """
    MiscStorage().delete(identifier)


def preview_thumbnail(identifier, filename):
    """Send a thumbnail to a client for previewing.

    Uses the :class:`.MiscStorage` to send the thumbnails.

    :param identifier: A file identifier that will be passed to the storage in order to
        send the thumbnail.
    :param filename: The name of the thumbnail to send.
    :return: The response object.
    """
    return MiscStorage().download(
        identifier, filename=filename, mimetype=const.MIMETYPE_JPEG, as_attachment=False
    )
