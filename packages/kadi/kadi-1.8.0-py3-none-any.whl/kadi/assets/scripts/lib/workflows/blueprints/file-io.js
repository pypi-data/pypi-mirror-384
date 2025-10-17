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

import {NodeBlueprint, commonInputs, commonOutputs, sockets} from 'scripts/lib/workflows/core.js';
import {BoolControl} from 'scripts/lib/workflows/controls.js';
import {BuiltinNode} from 'scripts/lib/workflows/nodes.js';

class FileIONode extends BuiltinNode {
  static group = 'File I/O';
}

class FileOutputNode extends FileIONode {
  constructor(editor, name) {
    super(
      editor,
      name,
      'File Output',
      [commonInputs.dep, {key: 'path', title: 'File Path'}, {key: 'append', socket: sockets.bool}, commonInputs.pipe],
      [commonOutputs.dep],
    );

    this.shortcutControl = new BoolControl(this.triggerChange.bind(this), 'Shortcut');
    this.addControl('shortcut', this.shortcutControl);
  }

  dump() {
    const data = super.dump();
    data.model.createShortcut = this.shortcutControl.value;
    return data;
  }

  load(data) {
    super.load(data);
    this.shortcutControl.setValue(data.model.createShortcut);
  }
}

const fileInput = new NodeBlueprint(
  FileIONode,
  'FileInput',
  'File Input',
  [commonInputs.dep, {key: 'path', title: 'File Path'}],
  [commonOutputs.dep, commonOutputs.pipe],
);

export default [fileInput, new NodeBlueprint(FileOutputNode, 'FileOutput')];
