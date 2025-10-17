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

import {BuiltinNode} from 'scripts/lib/workflows/nodes.js';
import {NodeBlueprint} from 'scripts/lib/workflows/core.js';

class AnnotationNode extends BuiltinNode {
  static group = 'Annotation';
}

class NoteNode extends AnnotationNode {
  constructor(editor, name) {
    super(editor, name, 'Note');
    this.text = '';
  }

  setText(text) {
    const prevText = this.text;
    this.text = String(text);

    if (this.text !== prevText) {
      this.triggerChange();
    }
  }

  dump() {
    const data = super.dump();
    data.model.text = this.text;
    return data;
  }

  load(data) {
    super.load(data);
    this.setText(data.model.text);
  }
}

export default [new NodeBlueprint(NoteNode, 'Note')];
