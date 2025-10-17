/* Copyright 2020 Karlsruhe Institute of Technology
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

import {ClassicPreset, NodeEditor} from 'rete';
import {NodeBlueprint} from 'scripts/lib/workflows/core.js';
import {ToolNode} from 'scripts/lib/workflows/nodes.js';

export default class WorkflowEditor extends NodeEditor {
  constructor(registry, area, changeCallback = null) {
    super('WorkflowEditor');

    this.registry = registry;
    this.area = area;
    this.variables = [];

    const changeEvents = ['nodecreated', 'noderemoved', 'connectioncreated', 'connectionremoved', 'unsavedchange'];

    this.addPipe((context) => {
      if (context.type === 'connectioncreate') {
        if (!this.validateConnection(context.data)) {
          return false;
        }
      }

      if (changeCallback && changeEvents.includes(context.type)) {
        changeCallback();
      }

      return context;
    });
  }

  setVariables(variables) {
    this.variables = variables;
  }

  validateConnection(connection) {
    const duplicateConnection = this.getConnections().find((c) => {
      return (c.source === connection.source)
        && (c.sourceOutput === connection.sourceOutput)
        && (c.target === connection.target)
        && (c.targetInput === connection.targetInput);
    });

    if (duplicateConnection) {
      return false;
    }

    const sourceNode = this.getNode(connection.source);
    const outputSocket = sourceNode.outputs[connection.sourceOutput].socket;
    const targetNode = this.getNode(connection.target);
    const inputSocket = targetNode.inputs[connection.targetInput].socket;

    return (sourceNode !== targetNode) && outputSocket.compatibleWith(inputSocket);
  }

  dump() {
    const data = {
      nodes: [],
      connections: [],
      variables: this.variables,
    };

    for (const node of this.getNodes()) {
      data.nodes.push(node.dump());
    }

    for (const connection of this.getConnections()) {
      const sourceNode = this.getNode(connection.source);
      const outputIndex = sourceNode.outputs[connection.sourceOutput].index;
      const targetNode = this.getNode(connection.target);
      const inputIndex = targetNode.inputs[connection.targetInput].index;

      data.connections.push({
        out_id: sourceNode.id,
        out_index: outputIndex,
        in_id: targetNode.id,
        in_index: inputIndex,
      });
    }

    return data;
  }

  async load(data) {
    for (const nodeData of data.nodes) {
      let name = nodeData.model.name;

      if (ToolNode.isToolNode(name)) {
        const tool = ToolNode.toolFromData(nodeData);
        name = ToolNode.nameFromTool(tool);

        if (!this.registry.has(name)) {
          const blueprint = new NodeBlueprint(ToolNode, name, tool);
          this.registry.register(blueprint);
        }
      }

      let node = null;

      try {
        node = this.registry.create(name, this);
      } catch (error) {
        console.error(error);
        continue;
      }

      node.load(nodeData);

      await this.addNode(node);
      await this.area.translate(node.id, {x: nodeData.position.x, y: nodeData.position.y});
    }

    for (const connectionData of data.connections) {
      const sourceNode = this.getNode(connectionData.out_id);
      const targetNode = this.getNode(connectionData.in_id);

      if (!sourceNode || !targetNode) {
        continue;
      }

      const outputKey = sourceNode.getOutputKey(connectionData.out_index);
      const inputKey = targetNode.getInputKey(connectionData.in_index);
      const connection = new ClassicPreset.Connection(sourceNode, outputKey, targetNode, inputKey);

      await this.addConnection(connection);
    }

    if (data.variables) {
      this.setVariables(data.variables);
    }
  }
}
