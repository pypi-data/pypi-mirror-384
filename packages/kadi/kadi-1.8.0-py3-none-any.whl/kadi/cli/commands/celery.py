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
import click
from celery.bin.celery import celery as celery_cmd

from kadi.cli.main import kadi
from kadi.cli.utils import check_database


# This wrapper command ensures that the correct Celery application is being used and
# that it gets initialized correctly by creating the Flask application as normal. It
# also leads to an application context being pushed, which is needed for the pre- and
# post-run handlers, while the tasks themselves run in their own application context.
@kadi.command(
    context_settings={
        "allow_extra_args": True,
        "ignore_unknown_options": True,
    }
)
@click.pass_context
def celery(ctx):
    """Wrapper command for Celery.

    For a list of subcommands and additional parameters that can be passed to Celery,
    please run "celery --help".
    """
    check_database()
    # pylint: disable=no-value-for-parameter
    celery_cmd(["--app", "kadi.ext.celery:celery", *ctx.args])
