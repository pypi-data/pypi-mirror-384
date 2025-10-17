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

import {NodeBlueprint, commonInputs, commonOutputs} from 'scripts/lib/workflows/core.js';
import {BuiltinNode} from 'scripts/lib/workflows/nodes.js';

class UserOutputNode extends BuiltinNode {
  static group = 'User Output';
}

const userOutputText = new NodeBlueprint(
  UserOutputNode,
  'UserOutputText',
  'User Output: Text',
  [commonInputs.dep, {key: 'file', title: 'Text File', required: true}],
  [commonOutputs.dep],
);

const userOutputWebView = new NodeBlueprint(
  UserOutputNode,
  'UserOutputWebView',
  'User Output: WebView',
  [commonInputs.dep, {key: 'description'}, {key: 'url', title: 'URL'}],
  [commonOutputs.dep],
);

export default [userOutputText, userOutputWebView];
