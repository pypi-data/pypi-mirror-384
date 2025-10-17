/* Copyright 2024 Karlsruhe Institute of Technology
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License. */

import {BoolControl, StringControl} from 'scripts/lib/workflows/controls.js';
import {NodeBlueprint, sockets} from 'scripts/lib/workflows/core.js';
import {BuiltinNode} from 'scripts/lib/workflows/nodes.js';

class SourceNode extends BuiltinNode {
  static group = 'Source';

  constructor(editor, name, socket, control) {
    super(editor, name, '', [], [{key: 'value', title: name, socket, multi: true}]);

    // eslint-disable-next-line new-cap
    this.control = new control(this.triggerChange.bind(this));
    this.addControl('value', this.control);
  }

  dump() {
    const data = super.dump();

    // All values are stored as strings.
    if (this.value === null) {
      data.model.value = '';
    } else {
      data.model.value = String(this.control.value);
    }

    return data;
  }

  load(data) {
    super.load(data);
    this.control.setValue(data.model.value);
  }
}

export default [
  new NodeBlueprint(SourceNode, 'Boolean', sockets.bool, BoolControl),
  new NodeBlueprint(SourceNode, 'Float', sockets.float, StringControl),
  new NodeBlueprint(SourceNode, 'Integer', sockets.int, StringControl),
  new NodeBlueprint(SourceNode, 'String', sockets.str, StringControl),
];
