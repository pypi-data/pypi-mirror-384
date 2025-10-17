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
from flask import render_template
from jinja2 import nodes
from jinja2.ext import Extension


class SnippetExtension(Extension):
    """Jinja extension to easily pass variables to HTML snippets.

    **Example:**

    .. code-block:: jinja

        {% snippet "my_snippet.html", foo=1, bar=2 %}
    """

    tags = {"snippet"}

    def parse(self, parser):
        """Parse the snippet tag and arguments."""
        kwargs = []

        # Token that started the tag.
        tag = next(parser.stream)

        # Parse the snippet name.
        name = parser.parse_expression()

        # If there is a comma, additional key/value arguments have been provided.
        if parser.stream.skip_if("comma"):
            while parser.stream.current.type != "block_end":
                if kwargs:
                    parser.stream.expect("comma")

                # Key of the argument.
                key = next(parser.stream)
                key = nodes.Const(key.value, lineno=key.lineno)

                # Assignment of the argument.
                parser.stream.expect("assign")

                # Value of the argument.
                value = parser.parse_expression()
                kwargs.append(nodes.Pair(key, value, lineno=key.lineno))

        return nodes.CallBlock(
            self.call_method("_render_snippet", [name, nodes.Dict(kwargs)]), [], [], []
        ).set_lineno(tag.lineno)

    def _render_snippet(self, name, kwargs, caller):
        return render_template(name, **kwargs)
