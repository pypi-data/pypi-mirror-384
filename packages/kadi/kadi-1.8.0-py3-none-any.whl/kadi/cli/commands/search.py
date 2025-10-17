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
import sys

import click
from elasticsearch.exceptions import NotFoundError
from flask import current_app

import kadi.lib.constants as const
from kadi.cli.main import kadi
from kadi.cli.utils import echo
from kadi.cli.utils import echo_danger
from kadi.cli.utils import echo_success
from kadi.cli.utils import echo_warning
from kadi.ext.db import db
from kadi.ext.elasticsearch import es
from kadi.lib.db import get_class_by_tablename
from kadi.lib.search.core import add_to_index
from kadi.lib.search.core import create_index
from kadi.lib.search.models import SearchableMixin
from kadi.lib.utils import as_list


@kadi.group()
def search():
    """Utility commands for managing search indices."""


def _get_searchable_models(tablename=None):
    # A single tablename was given, try to find a fitting searchable model.
    if tablename:
        model = get_class_by_tablename(tablename)

        if model is None or not issubclass(model, SearchableMixin):
            echo_warning(f"'{tablename}' is not a searchable model.")
            sys.exit(1)

        return [model]

    # No tablename was given, so all searchable models are collected.
    models = []

    for _tablename in db.metadata.tables.keys():
        model = get_class_by_tablename(_tablename)

        if model is not None and issubclass(model, SearchableMixin):
            models.append(model)

    return models


@search.command()
def init():
    """Create the search indices for all searchable models."""
    for model in _get_searchable_models():
        if create_index(model) is None:
            echo_danger(f"Error creating index for '{model.__tablename__}'.")
            sys.exit(1)

    echo_success("Search indices created successfully.")


@search.command()
def ls():
    """List the search indices for all searchable models."""
    for model in _get_searchable_models():
        tablename = model.__tablename__

        echo(f"Indices for '{tablename}':", bold=True)

        try:
            current_index = list(es.indices.get_alias(index=tablename).keys())[0]
        except:
            current_index = None

        for index in es.indices.get(index=f"{tablename}*").keys():
            if index == current_index:
                echo(f"* {index} (pointed to by alias '{tablename}')")
            else:
                echo(f"* {index}")


@search.command()
@click.option(
    "-m",
    "--model",
    "tablename",
    help="The name of a searchable model whose index should be rebuilt.",
    type=click.Choice(list(const.RESOURCE_TYPES)),
)
@click.option("--i-am-sure", is_flag=True)
def reindex(tablename, i_am_sure):
    """Rebuild the search indices for all searchable models.

    This will create a new search index for each searchable model, populate it and
    switch it with the current one afterwards.
    """
    if not i_am_sure:
        hosts = current_app.config["ELASTICSEARCH_HOSTS"]
        hosts = as_list(hosts)

        echo_warning(
            "This might rebuild one or more search indices of instance(s)"
            f" '{', '.join(hosts)}'. If you are sure you want to do this, use the flag"
            " --i-am-sure."
        )
        sys.exit(1)

    for model in _get_searchable_models(tablename):
        tablename = model.__tablename__

        echo(f"Rebuilding index for '{tablename}'.", bold=True)

        # Make sure an initial index always exists.
        if not create_index(model):
            echo_danger(f"Error creating initial index for '{tablename}'.")
            sys.exit(1)

        old_index = list(es.indices.get_alias(index=tablename).keys())[0]
        new_index = create_index(model, force=True)

        if new_index is None:
            echo_danger(f"Error creating new index for '{tablename}'.")
            sys.exit(1)

        # Populate the new index.
        model_query = model.query
        echo(
            f"Populating new index '{new_index}' with {model_query.count()}"
            f" {tablename}(s)..."
        )

        for obj in model_query.order_by("created_at"):
            if not add_to_index(obj, index=new_index):
                echo_warning(f"Error indexing {tablename} with ID '{obj.id}'.")

        # Switch the alias to only point to the new index.
        es.indices.update_aliases(
            actions=[
                {"remove": {"index": old_index, "alias": tablename}},
                {"add": {"index": new_index, "alias": tablename}},
            ]
        )
        # Now the old index can be safely deleted.
        es.indices.delete(index=old_index)

        echo(
            f"Moved alias '{tablename}' from old index '{old_index}' to new index"
            f" '{new_index}'."
        )

    echo_success("Search indices rebuilt successfully.")


@search.command()
@click.argument("index")
@click.option("--i-am-sure", is_flag=True)
def remove(index, i_am_sure):
    """Remove one or more specified search indices.

    Note that the given INDEX supports wildcards in the form of asterisks.
    """
    if not i_am_sure:
        hosts = current_app.config["ELASTICSEARCH_HOSTS"]
        hosts = as_list(hosts)

        echo_warning(
            f"This might remove one or more search indices of instance(s)"
            f" '{', '.join(hosts)}'. If you are sure you want to do this, use the flag"
            " --i-am-sure."
        )
        sys.exit(1)

    try:
        indices = list(es.indices.get(index=index).keys())

        if not indices:
            echo_warning(f"No indices found for '{index}'.")
            sys.exit(1)

        for _index in indices:
            echo(f"Removing index '{_index}'...")
            es.indices.delete(index=_index)

    except NotFoundError:
        echo_warning(f"No indices found for '{index}'.")
        sys.exit(1)

    echo_success("Search indices removed successfully.")
