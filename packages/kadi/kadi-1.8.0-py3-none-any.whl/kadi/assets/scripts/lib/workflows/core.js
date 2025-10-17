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

export class NodeBlueprint {
  constructor(type, name, ...args) {
    this.type = type;
    this.name = name;
    this.args = args;
  }

  create(editor) {
    // eslint-disable-next-line new-cap
    return new this.type(editor, this.name, ...this.args);
  }
}

export class NodeRegistry {
  constructor() {
    this.blueprints = {};
  }

  has(name) {
    return (name in this.blueprints);
  }

  register(blueprint) {
    if (this.has(blueprint.name)) {
      throw new Error(`Node blueprint '${blueprint.name}' is already registered.`);
    }

    this.blueprints[blueprint.name] = blueprint;
  }

  create(name, editor) {
    if (!this.has(name)) {
      throw new Error(`Node blueprint '${name}' is not registered.`);
    }

    return this.blueprints[name].create(editor);
  }
}

export class Input extends ClassicPreset.Input {
  constructor(index, socket, label, multipleConnections = false, required = false, param = null) {
    super(socket, label, multipleConnections);

    this.index = index;
    this.required = required;
    this.param = param;
  }
}

export class Output extends ClassicPreset.Output {
  constructor(index, socket, label, multipleConnections = false) {
    super(socket, label, multipleConnections);
    this.index = index;
  }
}

class Socket extends ClassicPreset.Socket {
  constructor(name, compatibleNames = []) {
    super(name);
    this.compatibleNames = compatibleNames;
  }

  compatibleWith(socket) {
    return this.compatibleNames.includes(socket.name) || (this.name === socket.name);
  }
}

export const sockets = {
  str: new Socket('str', ['int', 'float', 'bool']),
  int: new Socket('int', ['str', 'float']),
  float: new Socket('float', ['str', 'int']),
  bool: new Socket('bool', ['str']),
  dep: new Socket('dep'),
  pipe: new Socket('pipe', ['str', 'int', 'float', 'bool']),
  env: new Socket('env'),
};

export const commonInputs = {
  dep: {key: 'dependency', title: 'Dependencies', socket: sockets.dep, multi: true},
  pipe: {key: 'pipe', title: 'stdin', socket: sockets.pipe},
  env: {key: 'env', title: 'env', socket: sockets.env},
};

export const commonOutputs = {
  dep: {key: 'dependency', title: 'Dependents', socket: sockets.dep, multi: true},
  pipe: {key: 'pipe', title: 'stdout', socket: sockets.pipe},
  env: {key: 'env', title: 'env', socket: sockets.env},
};
