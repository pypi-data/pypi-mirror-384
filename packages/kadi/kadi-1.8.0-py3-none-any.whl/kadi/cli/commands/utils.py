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
import subprocess
import sys

import click
from flask import current_app
from jinja2 import Template

from kadi.cli.main import kadi
from kadi.cli.utils import check_env
from kadi.cli.utils import echo
from kadi.cli.utils import echo_danger
from kadi.cli.utils import echo_success


DEFAULT_USER = "kadi"
DEFAULT_GROUP = "kadi"
DEFAULT_CONFIG_FILE = "/opt/kadi/config/kadi.py"
DEFAULT_INI_FILE = "/etc/kadi-uwsgi.ini"
DEFAULT_CERT_FILE = "/etc/ssl/certs/kadi.crt"
DEFAULT_KEY_FILE = "/etc/ssl/private/kadi.key"


@kadi.group()
def utils():
    """Miscellaneous utility commands."""


@utils.command()
def config():
    """Print the current Kadi configuration."""
    for key, value in sorted(current_app.config.items()):
        echo(f"{key}: {value}")


@utils.command()
@click.option("-p", "--port", help="The port to bind to.", default=8_025)
@check_env
def smtpd(port):
    """Run a simple SMTP server for debugging purposes."""
    echo(f"Listening on localhost:{port}...")

    try:
        subprocess.run(["python", "-m", "aiosmtpd", "-n", "-l", f"localhost:{port}"])
    except KeyboardInterrupt:
        pass


def _generate_config(template_name, outfile=None, **kwargs):
    template_path = os.path.join(
        current_app.root_path, "cli", "templates", template_name
    )

    with open(template_path, encoding="utf-8") as f:
        template = Template(f.read())

    rendered_template = template.render(**kwargs)

    if outfile is not None:
        if os.path.exists(outfile.name):
            echo_danger(f"'{outfile.name}' already exists.")
            sys.exit(1)

        outfile.write(f"{rendered_template}\n")
        echo_success(f"File '{outfile.name}' generated successfully.")
    else:
        echo(f"\n{rendered_template}", bold=True)


@utils.command()
@click.option(
    "-d", "--default", is_flag=True, help="Use the default values for all prompts."
)
@click.option(
    "-o", "--out", type=click.File(mode="w"), help="Output file (e.g. kadi.conf)."
)
def apache(default, out):
    """Generate a basic Apache web server configuration."""
    DEFAULT_CHAIN_FILE = ""

    if default:
        cert_file = DEFAULT_CERT_FILE
        key_file = DEFAULT_KEY_FILE
        chain_file = DEFAULT_CHAIN_FILE
    else:
        cert_file = click.prompt("SSL/TLS certificate file", default=DEFAULT_CERT_FILE)
        key_file = click.prompt("SSL/TLS key file", default=DEFAULT_KEY_FILE)
        chain_file = click.prompt(
            "SSL/TLS intermediate certificates chain file (optional)",
            default=DEFAULT_CHAIN_FILE,
        )

    anonip_bin = None

    if default or click.confirm(
        "Anonymize IP addresses in access logs using the 'anonip' Python package?",
        default=True,
    ):
        anonip_bin = os.path.join(sys.prefix, "bin", "anonip")

    _generate_config(
        "kadi.conf",
        outfile=out,
        server_name=current_app.config["SERVER_NAME"],
        storage_path=current_app.config["STORAGE_PATH"],
        misc_uploads_path=current_app.config["MISC_UPLOADS_PATH"],
        static_path=current_app.static_folder,
        cert_file=cert_file,
        key_file=key_file,
        chain_file=chain_file,
        anonip_bin=anonip_bin,
    )


@utils.command()
@click.option(
    "-d", "--default", is_flag=True, help="Use the default values for all prompts."
)
@click.option(
    "-o", "--out", type=click.File(mode="w"), help="Output file (e.g. kadi.ini)."
)
def uwsgi(default, out):
    """Generate a basic uWSGI application server configuration."""
    if default:
        uid = DEFAULT_USER
        gid = DEFAULT_GROUP
        kadi_config = DEFAULT_CONFIG_FILE
    else:
        uid = click.prompt("User the server will run under", default=DEFAULT_USER)
        gid = click.prompt("Group the server will run under", default=DEFAULT_GROUP)
        kadi_config = click.prompt(
            "Kadi configuration file", default=DEFAULT_CONFIG_FILE
        )

    _generate_config(
        "kadi-uwsgi.ini",
        outfile=out,
        num_processes=min(os.cpu_count() or 4, 50),
        root_path=current_app.root_path,
        venv_path=sys.prefix,
        uid=uid,
        gid=gid,
        kadi_config=kadi_config,
    )


@utils.command()
@click.option(
    "-d", "--default", is_flag=True, help="Use the default values for all prompts."
)
@click.option(
    "-o",
    "--out",
    type=click.File(mode="w"),
    help="Output file (e.g. kadi-uwsgi.service).",
)
def uwsgi_service(default, out):
    """Generate a basic systemd unit file for uWSGI."""
    if default:
        uid = DEFAULT_USER
        gid = DEFAULT_GROUP
        kadi_ini = DEFAULT_INI_FILE
    else:
        uid = click.prompt("User the service will run under", default=DEFAULT_USER)
        gid = click.prompt("Group the service will run under", default=DEFAULT_GROUP)
        kadi_ini = click.prompt("uWSGI configuration file", default=DEFAULT_INI_FILE)

    _generate_config(
        "kadi-uwsgi.service",
        outfile=out,
        uwsgi_bin=os.path.join(sys.prefix, "bin", "uwsgi"),
        uid=uid,
        gid=gid,
        kadi_ini=kadi_ini,
    )


@utils.command()
@click.option(
    "-d", "--default", is_flag=True, help="Use the default values for all prompts."
)
@click.option(
    "-o",
    "--out",
    type=click.File(mode="w"),
    help="Output file (e.g. kadi-celery.service).",
)
def celery(default, out):
    """Generate a basic systemd unit file for Celery."""
    if default:
        uid = DEFAULT_USER
        gid = DEFAULT_GROUP
        kadi_config = DEFAULT_CONFIG_FILE
    else:
        uid = click.prompt("User the service will run under", default=DEFAULT_USER)
        gid = click.prompt("Group the service will run under", default=DEFAULT_GROUP)
        kadi_config = click.prompt(
            "Kadi configuration file", default=DEFAULT_CONFIG_FILE
        )

    _generate_config(
        "kadi-celery.service",
        outfile=out,
        kadi_bin=os.path.join(sys.prefix, "bin", "kadi"),
        uid=uid,
        gid=gid,
        kadi_config=kadi_config,
    )


@utils.command()
@click.option(
    "-d", "--default", is_flag=True, help="Use the default values for all prompts."
)
@click.option(
    "-o",
    "--out",
    type=click.File(mode="w"),
    help="Output file (e.g. kadi-celerybeat.service).",
)
def celerybeat(default, out):
    """Generate a basic systemd unit file for Celery Beat."""
    if default:
        uid = DEFAULT_USER
        gid = DEFAULT_GROUP
        kadi_config = DEFAULT_CONFIG_FILE
    else:
        uid = click.prompt("User the service will run under", default=DEFAULT_USER)
        gid = click.prompt("Group the service will run under", default=DEFAULT_GROUP)
        kadi_config = click.prompt(
            "Kadi configuration file", default=DEFAULT_CONFIG_FILE
        )

    _generate_config(
        "kadi-celerybeat.service",
        outfile=out,
        kadi_bin=os.path.join(sys.prefix, "bin", "kadi"),
        uid=uid,
        gid=gid,
        kadi_config=kadi_config,
    )
