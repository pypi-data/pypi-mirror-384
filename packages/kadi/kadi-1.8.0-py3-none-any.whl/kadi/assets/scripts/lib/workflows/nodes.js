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

import {ClassicPreset} from 'rete';

import {Input, Output, commonInputs, commonOutputs, sockets} from 'scripts/lib/workflows/core.js';

const builtinInputKeys = Object.values(commonInputs).map((input) => input.key);

export class BaseNode extends ClassicPreset.Node {
  static group = 'Ungrouped';

  constructor(editor, name, label) {
    super(label);

    this.editor = editor;
    this.name = name;

    this.id = `{${window.crypto.randomUUID()}}`;

    /* eslint-disable no-undefined */
    // Required properties for the arrange plugin. Must not be set initially.
    this.width = undefined;
    this.height = undefined;
    /* eslint-enable no-undefined */
  }

  _sortedEntries(prop) {
    return Object.entries(this[prop]).sort((a, b) => a[1].index - b[1].index);
  }

  _hasEntry(prop) {
    return Object.keys(this[prop]).length > 0;
  }

  _getPortKey(index, ports) {
    for (const [key, port] of Object.entries(ports)) {
      if (index === port.index) {
        return key;
      }
    }

    return null;
  }

  get position() {
    return this.editor.area.nodeViews.get(this.id).position;
  }

  get sortedInputs() {
    return this._sortedEntries('inputs');
  }

  get sortedOutputs() {
    return this._sortedEntries('outputs');
  }

  get sortedControls() {
    return this._sortedEntries('controls');
  }

  get hasInputs() {
    return this._hasEntry('inputs');
  }

  get hasOutputs() {
    return this._hasEntry('outputs');
  }

  get hasControls() {
    return this._hasEntry('controls');
  }

  getInputKey(index) {
    return this._getPortKey(index, this.inputs);
  }

  getOutputKey(index) {
    return this._getPortKey(index, this.outputs);
  }

  setWidth(width) {
    this.width = width;
  }

  setHeight(height) {
    this.height = height;
  }

  triggerChange() {
    this.editor.emit({type: 'unsavedchange'});
  }

  updateView() {
    this.editor.area.update('node', this.id);
  }

  dump() {
    return {
      id: this.id,
      model: {
        name: this.name,
      },
      position: {
        x: this.position.x,
        y: this.position.y,
      },
    };
  }

  load(data) {
    this.id = data.id;
  }
}

function makeInput(inputData, index, param = null) {
  const title = inputData.title || kadi.utils.capitalize(inputData.key);
  const socket = inputData.socket || sockets.str;
  const multi = inputData.multi || false;
  const required = inputData.required || false;

  return new Input(index, socket, title, multi, required, param);
}

function makeOutput(outputData, index) {
  const title = outputData.title || kadi.utils.capitalize(outputData.key);
  const socket = outputData.socket || sockets.str;
  const multi = outputData.multi || false;

  return new Output(index, socket, title, multi);
}

export class BuiltinNode extends BaseNode {
  constructor(editor, name, label, inputs = [], outputs = []) {
    super(editor, name, label);

    for (const [index, inputData] of inputs.entries()) {
      this.addInput(inputData.key, makeInput(inputData, index));
    }
    for (const [index, outputData] of outputs.entries()) {
      this.addOutput(outputData.key, makeOutput(outputData, index));
    }
  }
}

function inputFromParam(param, index) {
  let title = null;
  let socket = null;

  switch (param.type) {
    case 'int':
    case 'long':
      title = `Integer: ${param.name}`;
      socket = sockets.int;
      break;

    case 'float':
    case 'real':
      title = `Float: ${param.name}`;
      socket = sockets.float;
      break;

    case 'bool':
    case 'flag':
      title = `Boolean: ${param.name}`;
      socket = sockets.bool;
      break;

    default:
      title = `${kadi.utils.capitalize(param.type)}: ${param.name}`;
      socket = sockets.str;
  }

  return makeInput({title, socket, required: param.required}, index, param);
}

function dumpPort(key, io, direction, index) {
  const param = io.param;
  const data = {
    name: io.label,
    shortName: null,
    type: key,
    required: false,
    port_direction: direction,
    port_index: index,
  };

  if (param) {
    Object.assign(data, {
      name: param.name,
      shortName: param.char,
      type: param.type,
      required: param.required,
    });
  }

  return data;
}

export class ToolNode extends BaseNode {
  constructor(editor, name, tool) {
    super(editor, name, name);

    this.tool = tool;
    this.executionProfile = this.executionProfiles[0];

    const isProgram = tool.type === 'program';

    // Inputs.
    let index = 0;

    if (isProgram) {
      this.addInput(commonInputs.dep.key, makeInput(commonInputs.dep, index++));
    }

    const numInputs = Object.keys(this.inputs).length;

    for (const param of tool.params) {
      const input = inputFromParam(param, index);
      this.addInput(`param${index - numInputs}`, input);
      index++;
    }

    if (isProgram) {
      this.addInput(commonInputs.env.key, makeInput(commonInputs.env, index++));
      this.addInput(commonInputs.pipe.key, makeInput(commonInputs.pipe, index++));
    }

    // Outputs.
    index = 0;

    if (isProgram) {
      this.addOutput(commonOutputs.dep.key, makeOutput(commonOutputs.dep, index++));
      this.addOutput(commonOutputs.pipe.key, makeOutput(commonOutputs.pipe, index++));
    } else {
      this.addOutput(commonOutputs.env.key, makeOutput(commonOutputs.env, index++));
    }
  }

  static isToolNode(name) {
    return ['ToolNode', 'EnvNode'].includes(name);
  }

  static nameFromTool(tool) {
    if (tool.version !== null) {
      return `${tool.name} ${tool.version}`;
    }

    return tool.name;
  }

  static toolFromData(data) {
    const toolData = data.model.tool;
    const tool = {
      name: toolData.name,
      version: toolData.version,
      type: data.model.name === 'ToolNode' ? 'program' : 'env',
      params: [],
      path: toolData.path,
    };

    for (const port of data.model.tool.ports) {
      // Ignore built-in input and output ports.
      if (port.port_direction === 'out' || builtinInputKeys.includes(port.type)) {
        continue;
      }

      tool.params.push({
        name: port.name,
        type: port.type,
        char: port.shortName,
        required: port.required,
      });
    }

    return tool;
  }

  get executionProfiles() {
    return ['Default', 'Skip', 'Detached'];
  }

  setExecutionProfile(profile) {
    const prevProfile = this.executionProfile;

    if (this.executionProfiles.includes(profile)) {
      this.executionProfile = profile;
    }

    if (this.executionProfile !== prevProfile) {
      this.triggerChange();
    }
  }

  dump() {
    const data = super.dump();
    const ports = [];

    data.model.name = this.tool.type === 'program' ? 'ToolNode' : 'EnvNode';
    data.model.executionProfile = this.executionProfile;
    data.model.tool = {
      name: this.tool.name,
      version: this.tool.version,
      path: this.tool.path || this.tool.name,
      ports,
    };

    const inputs = this.sortedInputs;

    for (let index = 0; index < inputs.length; index++) {
      const [key, input] = inputs[index];
      ports.push(dumpPort(key, input, 'in', index));
    }

    const outputs = this.sortedOutputs;

    for (let index = 0; index < outputs.length; index++) {
      const [key, output] = outputs[index];
      ports.push(dumpPort(key, output, 'out', index));
    }

    return data;
  }

  load(data) {
    super.load(data);
    this.setExecutionProfile(data.model.executionProfile);
  }
}
