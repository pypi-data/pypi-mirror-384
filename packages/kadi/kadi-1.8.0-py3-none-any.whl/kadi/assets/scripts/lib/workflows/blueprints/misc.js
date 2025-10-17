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

import {FormatControl, PortControl} from 'scripts/lib/workflows/controls.js';
import {Input, NodeBlueprint, commonInputs, commonOutputs, sockets} from 'scripts/lib/workflows/core.js';
import {BuiltinNode} from 'scripts/lib/workflows/nodes.js';

class MiscNode extends BuiltinNode {
  static group = 'Miscellaneous';
}

class FormatStringNode extends MiscNode {
  constructor(editor, name) {
    const inputs = [commonInputs.dep];
    const outputs = [commonOutputs.dep, {key: 'formattedString', title: 'Formatted String', multi: true}];

    super(editor, name, 'Format String', inputs, outputs);

    this.inputStartIndex = inputs.length;
    this.numPrevInputs = 0;

    this.inputControl = new PortControl(this.updateInputs.bind(this), 'Inputs');
    this.formatControl = new FormatControl(this.triggerChange.bind(this), 'Format');

    this.addControl('inputs', this.inputControl);
    this.addControl('format', this.formatControl);

    this.updateInputs();
  }

  async updateInputs() {
    const numInputs = this.inputControl.value;

    if (numInputs === this.numPrevInputs) {
      return;
    }

    const prefix = 'input';

    if (numInputs > this.numPrevInputs) {
      for (let i = this.numPrevInputs; i < numInputs; i++) {
        const input = new Input(this.inputStartIndex + i, sockets.str, `%${i}`);
        this.addInput(`${prefix}${i}`, input);
      }
    } else {
      const incomingConnections = this.editor.connections.filter((c) => c.target === this.id);

      for (let i = this.numPrevInputs; i > numInputs; i--) {
        const key = `${prefix}${i - 1}`;
        const connections = incomingConnections.filter((c) => c.targetInput === key);

        for (const connection of connections) {
          await this.editor.removeConnection(connection.id);
        }

        this.removeInput(key);
      }
    }

    this.numPrevInputs = numInputs;
    this.formatControl.updateDefaultValue(numInputs);

    this.triggerChange();
    this.updateView();
  }

  dump() {
    const data = super.dump();

    data.model.nInputs = this.inputControl.value;
    data.model.value = this.formatControl.value;

    return data;
  }

  load(data) {
    super.load(data);

    this.inputControl.setValue(data.model.nInputs);
    this.formatControl.setValue(data.model.value);

    this.updateInputs();
  }
}

export default [new NodeBlueprint(FormatStringNode, 'FormatString')];
