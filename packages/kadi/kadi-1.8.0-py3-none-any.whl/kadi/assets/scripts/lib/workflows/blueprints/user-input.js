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

import {Input, NodeBlueprint, commonInputs, commonOutputs, sockets} from 'scripts/lib/workflows/core.js';
import {BuiltinNode} from 'scripts/lib/workflows/nodes.js';
import {PortControl} from 'scripts/lib/workflows/controls.js';

class UserInputNode extends BuiltinNode {
  static group = 'User Input';
}

class UserInputChooseNode extends UserInputNode {
  constructor(editor, name) {
    const inputs = [commonInputs.dep, {key: 'prompt'}, {key: 'default', socket: sockets.int}];
    const outputs = [
      commonOutputs.dep,
      {key: 'selected', socket: sockets.int, multi: true},
      {key: 'value', multi: true},
    ];

    super(editor, name, 'User Input: Choose', inputs, outputs);

    this.optionStartIndex = inputs.length;
    this.numPrevOptions = 0;
    this.optionControl = new PortControl(this.updateOptions.bind(this), 'Options');

    this.addControl('options', this.optionControl);
    this.updateOptions();
  }

  async updateOptions() {
    const numOptions = this.optionControl.value;

    if (numOptions === this.numPrevOptions) {
      return;
    }

    const prefix = 'option';

    if (numOptions > this.numPrevOptions) {
      for (let i = this.numPrevOptions; i < numOptions; i++) {
        const input = new Input(this.optionStartIndex + i, sockets.str, `Option ${i + 1}`);
        this.addInput(`${prefix}${i}`, input);
      }
    } else {
      const incomingConnections = this.editor.connections.filter((c) => c.target === this.id);

      for (let i = this.numPrevOptions; i > numOptions; i--) {
        const key = `${prefix}${i - 1}`;
        const connections = incomingConnections.filter((c) => c.targetInput === key);

        for (const connection of connections) {
          await this.editor.removeConnection(connection.id);
        }

        this.removeInput(key);
      }
    }

    this.numPrevOptions = numOptions;

    this.triggerChange();
    this.updateView();
  }

  dump() {
    const data = super.dump();
    data.model.nOptions = this.optionControl.value;
    return data;
  }

  load(data) {
    super.load(data);

    this.optionControl.setValue(data.model.nOptions);
    this.updateOptions();
  }
}

const userInputBool = new NodeBlueprint(
  UserInputNode,
  'UserInputBool',
  'User Input: Bool',
  [commonInputs.dep, {key: 'prompt'}, {key: 'default', socket: sockets.bool}],
  [commonOutputs.dep, {key: 'value', multi: true, socket: sockets.bool}],
);

const userInputFile = new NodeBlueprint(
  UserInputNode,
  'UserInputFile',
  'User Input: File',
  [commonInputs.dep, {key: 'prompt'}, {key: 'default'}],
  [commonOutputs.dep, {key: 'value', multi: true}],
);

const userInputFloat = new NodeBlueprint(
  UserInputNode,
  'UserInputFloat',
  'User Input: Float',
  [commonInputs.dep, {key: 'prompt'}, {key: 'default', socket: sockets.float}],
  [commonOutputs.dep, {key: 'value', multi: true, socket: sockets.float}],
);

const userInputForm = new NodeBlueprint(
  UserInputNode,
  'UserInputForm',
  'User Input: Form',
  [commonInputs.dep, {key: 'jsonFile', title: 'JSON File'}],
  [commonOutputs.dep, {key: 'jsonString', title: 'JSON String', multi: true}],
);

const userInputInteger = new NodeBlueprint(
  UserInputNode,
  'UserInputInteger',
  'User Input: Integer',
  [commonInputs.dep, {key: 'prompt'}, {key: 'default', socket: sockets.int}],
  [commonOutputs.dep, {key: 'value', multi: true, socket: sockets.int}],
);

const userInputPeriodicTable = new NodeBlueprint(
  UserInputNode,
  'UserInputPeriodicTable',
  'User Input: Periodic Table',
  [commonInputs.dep, {key: 'prompt'}, {key: 'default'}],
  [commonOutputs.dep, {key: 'selectedElements', title: 'Selected Elements', multi: true}],
);

const userInputSelect = new NodeBlueprint(
  UserInputNode,
  'UserInputSelect',
  'User Input: Select',
  [commonInputs.dep, {key: 'prompt'}, {key: 'values'}, {key: 'default'}, {key: 'delimiter', title: 'Delimiter [,]'}],
  [commonOutputs.dep, {key: 'value', multi: true}],
);

const userInputSelectBoundingBox = new NodeBlueprint(
  UserInputNode,
  'UserInputSelectBoundingBox',
  'User Input: Select Bounding Box',
  [commonInputs.dep, {key: 'prompt'}, {key: 'imagePath', title: 'Image Path'}],
  [
    commonOutputs.dep,
    {key: 'x', socket: sockets.int, multi: true},
    {key: 'y', socket: sockets.int, multi: true},
    {key: 'width', socket: sockets.int, multi: true},
    {key: 'height', socket: sockets.int, multi: true},
  ],
);

const userInputText = new NodeBlueprint(
  UserInputNode,
  'UserInputText',
  'User Input: Text',
  [commonInputs.dep, {key: 'prompt'}, {key: 'default'}, {key: 'multiline', socket: sockets.bool}],
  [commonOutputs.dep, {key: 'value', multi: true}],
);

export default [
  userInputBool,
  new NodeBlueprint(UserInputChooseNode, 'UserInputChoose'),
  userInputFile,
  userInputFloat,
  userInputForm,
  userInputInteger,
  userInputPeriodicTable,
  userInputSelect,
  userInputSelectBoundingBox,
  userInputText,
];
