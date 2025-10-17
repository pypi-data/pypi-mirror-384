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

import {NodeBlueprint, Output, commonInputs, commonOutputs, sockets} from 'scripts/lib/workflows/core.js';
import {BuiltinNode} from 'scripts/lib/workflows/nodes.js';
import {PortControl} from 'scripts/lib/workflows/controls.js';

class ControlNode extends BuiltinNode {
  static group = 'Control';
}

class BranchSelectNode extends ControlNode {
  constructor(editor, name) {
    const inputs = [commonInputs.dep, {key: 'selected', socket: sockets.int}];
    const outputs = [commonOutputs.dep];

    super(editor, name, 'Branch Select', inputs, outputs);

    this.branchStartIndex = outputs.length;
    this.numPrevBranches = 0;
    this.branchControl = new PortControl(this.updateBranches.bind(this), 'Branches');

    this.addControl('branches', this.branchControl);
    this.updateBranches();
  }

  async updateBranches() {
    const numBranches = this.branchControl.value;

    if (numBranches === this.numPrevBranches) {
      return;
    }

    const prefix = 'branch';

    if (numBranches > this.numPrevBranches) {
      for (let i = this.numPrevBranches; i < numBranches; i++) {
        const output = new Output(this.branchStartIndex + i, sockets.dep, `Branch ${i + 1}`);
        this.addOutput(`${prefix}${i}`, output);
      }
    } else {
      const outgoingConnections = this.editor.connections.filter((c) => c.source === this.id);

      for (let i = this.numPrevBranches; i > numBranches; i--) {
        const key = `${prefix}${i - 1}`;
        const connections = outgoingConnections.filter((c) => c.sourceOutput === key);

        for (const connection of connections) {
          await this.editor.removeConnection(connection.id);
        }

        this.removeOutput(key);
      }
    }

    this.numPrevBranches = numBranches;

    this.triggerChange();
    this.updateView();
  }

  dump() {
    const data = super.dump();
    data.model.nBranches = this.branchControl.value;
    return data;
  }

  load(data) {
    super.load(data);

    this.branchControl.setValue(data.model.nBranches);
    this.updateBranches();
  }
}

const ifBranch = new NodeBlueprint(
  ControlNode,
  'IfBranch',
  'If-Branch',
  [commonInputs.dep, {key: 'condition', socket: sockets.bool}],
  [
    commonOutputs.dep,
    {key: 'true', socket: sockets.dep, multi: true},
    {key: 'false', socket: sockets.dep, multi: true},
  ],
);

const loop = new NodeBlueprint(
  ControlNode,
  'Loop',
  'Loop',
  [
    commonInputs.dep,
    {key: 'condition', socket: sockets.bool},
    {key: 'startIndex', title: 'Start Index [0]', socket: sockets.int},
    {key: 'endIndex', title: 'End Index', socket: sockets.int},
    {key: 'step', title: 'Step [1]', socket: sockets.int},
    {key: 'indexVarName', title: 'Index Variable Name'},
  ],
  [
    commonOutputs.dep,
    {key: 'loop', socket: sockets.dep, multi: true},
    {key: 'index', socket: sockets.int, multi: true},
  ],
);

const variable = new NodeBlueprint(
  ControlNode,
  'Variable',
  'Variable',
  [commonInputs.dep, {key: 'name', required: true}, {key: 'value'}],
  [commonOutputs.dep],
);

const variableList = new NodeBlueprint(
  ControlNode,
  'VariableList',
  'Variable List',
  [commonInputs.dep, {key: 'names', required: true}, {key: 'values'}, {key: 'delimiter', title: 'Delimiter [;]'}],
  [commonOutputs.dep],
);

const variableJson = new NodeBlueprint(
  ControlNode,
  'VariableJson',
  'Variable JSON',
  [commonInputs.dep, {key: 'jsonString', title: 'JSON String', required: true}, {key: 'key', title: 'Key ["data"]'}],
  [commonOutputs.dep],
);

export default [
  new NodeBlueprint(BranchSelectNode, 'BranchSelect'),
  ifBranch,
  loop,
  variable,
  variableList,
  variableJson,
];
