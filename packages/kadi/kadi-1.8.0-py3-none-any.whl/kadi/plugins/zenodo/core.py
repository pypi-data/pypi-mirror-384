# Copyright 2022 Karlsruhe Institute of Technology
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
from flask import render_template
from flask_babel import gettext as _
from flask_babel import lazy_gettext as _l

import kadi.lib.constants as const
from kadi.ext.db import db
from kadi.lib.conversion import markdown_to_html
from kadi.lib.forms import BaseForm
from kadi.lib.forms import JSONField
from kadi.lib.resources.utils import get_linked_resources
from kadi.lib.utils import utcnow
from kadi.modules.records.export import RecordROCrate
from kadi.modules.records.extras import ExtrasField
from kadi.modules.records.extras import extras_to_plain_json
from kadi.modules.records.models import Record

from .constants import DEFAULT_LICENSE


class UploadCanceledException(Exception):
    """For exceptions related to canceled uploads."""


class ExportFilterField(JSONField):
    """Custom field to process and validate export filter data.

    Only performs some basic validation to make sure the overall structure of the filter
    is valid.
    """

    def __init__(self, *args, **kwargs):
        kwargs["default"] = {}
        super().__init__(*args, **kwargs)

    def process_formdata(self, valuelist):
        super().process_formdata(valuelist)

        if valuelist:
            if not isinstance(self.data, dict):
                self.data = self.default
                raise ValueError("Invalid data structure.")


class ZenodoForm(BaseForm):
    """Base form class for use in publishing resources via Zenodo."""

    class Meta:
        """Container to store meta class attributes."""

        csrf = False

    export_filter = ExportFilterField(_l("Customize export data"))

    extras = ExtrasField(_l("Customize import metadata"))


class UploadStream:
    """Helper class to handle uploading resource data as RO-Crate."""

    def __init__(self, record_or_records, resource, export_filter, user, task=None):
        self.ro_crate = RecordROCrate(
            record_or_records,
            resource.identifier,
            resource.title,
            genre=resource.__tablename__,
            export_filter=export_filter,
            user=user,
        )
        self.task = task

        # Total size of the data that was streamed so far.
        self._total_size = 0
        # Current size of the data that was streamed since the last time the task status
        # was checked, if applicable.
        self._current_size = 0

    def __iter__(self):
        for chunk in self.ro_crate:
            self._total_size += len(chunk)

            if self.task is not None:
                self._current_size += len(chunk)

                if self._current_size >= 10 * const.ONE_MB:
                    self._current_size = 0

                    if self.task.is_revoked:
                        raise UploadCanceledException

                    self.task.update_progress(self._total_size / len(self) * 100)
                    db.session.commit()

            yield chunk

    def __len__(self):
        return len(self.ro_crate)


def _delete_draft_record(draft_record, client, token):
    try:
        client.delete(f"records/{draft_record['id']}/draft", token=token)
    except:
        pass


def _make_error_template(message=None, response=None):
    status = response.status_code if response is not None else None

    if message is None:
        try:
            # If the email address of the account is not confirmed yet, no records can
            # be created. Unfortunately, Zenodo only returns an HTML response in this
            # case, so we try to catch that.
            if (
                response.status_code == 403
                and response.headers["Content-Type"]
                == f"{const.MIMETYPE_HTML}; charset=utf-8"
            ):
                message = _("Please verify your email address first.")
            else:
                message = response.json()["message"]
        except:
            message = _("Unknown error.")

    return render_template("zenodo/upload_error.html", message=message, status=status)


def _extract_basic_metadata(resource, user):
    creator_meta = {"type": "personal"}
    name = user.displayname.rsplit(" ", 1)

    if len(name) == 2:
        creator_meta.update({"given_name": name[0], "family_name": name[1]})
    else:
        creator_meta["family_name"] = name[0]

    if user.orcid:
        creator_meta["identifiers"] = [{"scheme": "orcid", "identifier": user.orcid}]

    license_meta = {"id": DEFAULT_LICENSE}

    if isinstance(resource, Record) and resource.license:
        # Zenodo uses lower case license IDs in its vocabulary.
        license_meta["id"] = resource.license.name.lower()

    return {
        "resource_type": {"id": "dataset"},
        "title": resource.title,
        "publication_date": utcnow().strftime("%Y-%m-%d"),
        "creators": [{"person_or_org": creator_meta}],
        "description": markdown_to_html(resource.description),
        "rights": [license_meta],
        "subjects": [{"subject": tag.name} for tag in resource.tags.order_by("name")],
        "publisher": "Zenodo",
    }


def upload_resource(resource, form_data, user, client, token, task):
    """Upload the given resource to Zenodo."""
    basic_metadata = _extract_basic_metadata(resource, user)
    custom_metadata = extras_to_plain_json(form_data["extras"])

    draft_record = None

    try:
        # Check if the extracted license is supported by Zenodo.
        license_meta = basic_metadata["rights"][0]
        response = client.get(
            f"vocabularies/licenses/{license_meta['id']}", token=token
        )

        if not response.ok:
            license_meta["id"] = DEFAULT_LICENSE

        basic_metadata |= custom_metadata.pop("metadata", {})
        community = custom_metadata.pop("community", None)
        metadata = {
            "metadata": basic_metadata,
            **custom_metadata,
        }

        # Create a new draft record using the InvenioRDM API.
        response = client.post("records", token=token, json=metadata)

        if not response.ok:
            return False, _make_error_template(response=response)

        draft_record = response.json()

        # If applicable, create a review request for the given community. This requires
        # retrieving the community ID first.
        if community:
            response = client.get(f"communities/{community}", token=token)

            if response.ok:
                response = client.put(
                    f"records/{draft_record['id']}/draft/review",
                    token=token,
                    json={
                        "receiver": {"community": response.json()["id"]},
                        "type": "community-submission",
                    },
                )

                if not response.ok:
                    _delete_draft_record(draft_record, client, token)
                    return False, _make_error_template(response=response)

        if isinstance(resource, Record):
            record_or_records = resource
        else:
            if form_data["export_filter"].get("records", False):
                record_or_records = []
            else:
                record_or_records = get_linked_resources(
                    Record, resource.records, user=user
                )

        # Initialize a file upload within the draft record.
        response = client.post(
            draft_record["links"]["files"],
            token=token,
            json=[{"key": f"{resource.identifier}.zip"}],
        )

        if not response.ok:
            _delete_draft_record(draft_record, client, token)
            return False, _make_error_template(response=response)

        # Upload the content of the file.
        stream = UploadStream(
            record_or_records, resource, form_data["export_filter"], user, task=task
        )
        response = client.put(
            response.json()["entries"][0]["links"]["content"],
            token=token,
            data=stream,
            headers={
                "Content-Type": const.MIMETYPE_BINARY,
                "Content-Length": str(len(stream)),
            },
        )

        if not response.ok:
            _delete_draft_record(draft_record, client, token)
            return False, _make_error_template(response=response)

        # Complete the file upload.
        response = client.post(response.json()["links"]["commit"], token=token)

        if not response.ok:
            _delete_draft_record(draft_record, client, token)
            return False, _make_error_template(response=response)

    except UploadCanceledException:
        _delete_draft_record(draft_record, client, token)
        return False, _("Upload canceled.")

    except Exception as e:
        current_app.logger.debug(e, exc_info=True)

        if draft_record is not None:
            _delete_draft_record(draft_record, client, token)

        return False, _make_error_template(message=repr(e))

    return True, render_template(
        "zenodo/upload_success.html", record_url=draft_record["links"]["self_html"]
    )
