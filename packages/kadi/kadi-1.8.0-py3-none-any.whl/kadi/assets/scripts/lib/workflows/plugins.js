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

import {AreaExtensions, AreaPlugin} from 'rete-area-plugin';
import {ConnectionPlugin, Presets as ConnectionPresets} from 'rete-connection-plugin';
import {Presets as RenderPresets, VuePlugin} from 'rete-vue-plugin';
import {ContextMenuPlugin} from 'rete-context-menu-plugin';

import {BoolControl, FormatControl, PortControl} from 'scripts/lib/workflows/controls.js';
import {BaseNode} from 'scripts/lib/workflows/nodes.js';
import WorkflowEditor from 'scripts/lib/workflows/editor.js';

import VueCheckboxControl from 'scripts/components/lib/workflows/controls/CheckboxControl.vue';
import VueConnection from 'scripts/components/lib/workflows/core/Connection.vue';
import VueFormatControl from 'scripts/components/lib/workflows/controls/FormatControl.vue';
import VueInputControl from 'scripts/components/lib/workflows/controls/InputControl.vue';
import VueMenu from 'scripts/components/lib/workflows/core/Menu.vue';
import VueNode from 'scripts/components/lib/workflows/core/Node.vue';
import VueNote from 'scripts/components/lib/workflows/core/Note.vue';
import VuePortControl from 'scripts/components/lib/workflows/controls/PortControl.vue';
import VueSocket from 'scripts/components/lib/workflows/core/Socket.vue';

export class CustomAreaPlugin extends AreaPlugin {
  constructor(container, editable, changeCallback = null) {
    super(container);

    this.clickPosition = {x: 0, y: 0};
    this.addPipe((context) => {
      if (context.type === 'zoom' && context.data.source === 'dblclick') {
        return false;
      }

      if (context.type === 'contextmenu') {
        if (!editable) {
          return false;
        }

        // Store the mouse position at the time the context menu was opened.
        this.clickPosition = this.area.pointer;
      }

      if (changeCallback && context.type === 'nodetranslated') {
        changeCallback();
      }

      return context;
    });

    AreaExtensions.simpleNodesOrder(this);
    AreaExtensions.selectableNodes(this, AreaExtensions.selector(), {accumulating: AreaExtensions.accumulateOnCtrl()});
    AreaExtensions.snapGrid(this, {size: 10});
  }
}

export class CustomConnectionPlugin extends ConnectionPlugin {
  constructor() {
    super();

    this.addPreset(ConnectionPresets.classic.setup());
    this.addPipe((context) => {
      const area = this.parentScope(AreaPlugin);
      const editor = area.parentScope(WorkflowEditor);

      if (context.type === 'connectionpick') {
        editor.emit({type: 'socket-validate', payload: context.data.socket.payload});
      }
      if (context.type === 'connectiondrop') {
        editor.emit({type: 'socket-reset'});
      }

      return context;
    });
  }
}

export class CustomRenderPlugin extends VuePlugin {
  constructor() {
    super();

    this.addPreset(RenderPresets.classic.setup({
      customize: {
        node(context) {
          if (context.payload.name === 'Note') {
            return VueNote;
          }

          return VueNode;
        },
        socket() {
          return VueSocket;
        },
        connection() {
          return VueConnection;
        },
        control(context) {
          const payload = context.payload;

          if (payload instanceof BoolControl) {
            return VueCheckboxControl;
          }
          if (payload instanceof PortControl) {
            return VuePortControl;
          }
          if (payload instanceof FormatControl) {
            return VueFormatControl;
          }

          return VueInputControl;
        },
      },
    }));

    this.addPreset({
      update(context) {
        const data = context.data;

        if (data.type === 'contextmenu') {
          return {
            items: data.items,
            searchBar: data.searchBar,
            onHide: data.onHide,
          };
        }

        return context;
      },
      render(context) {
        const data = context.data;

        if (data.type === 'contextmenu') {
          return {
            component: VueMenu,
            props: {
              items: data.items,
              searchBar: data.searchBar,
              onHide: data.onHide,
            },
          };
        }

        return context;
      },
    });
  }
}

function contextMenuItems(menuItems, context, plugin) {
  if (context === 'root') {
    return {
      searchBar: true,
      list: menuItems,
    };
  }

  const area = plugin.parentScope(AreaPlugin);
  const editor = area.parentScope(WorkflowEditor);

  const deleteItem = {
    key: 'delete',
    label: 'Delete',
    async handler() {
      if ('source' in context && 'target' in context) {
        await editor.removeConnection(context.id);
      } else {
        const nodeId = context.id;
        const connections = editor.getConnections().filter((c) => {
          return c.source === nodeId || c.target === nodeId;
        });

        for (const connection of connections) {
          await editor.removeConnection(connection.id);
        }

        await editor.removeNode(nodeId);
      }
    },
  };
  const cloneItem = {
    key: 'clone',
    label: 'Clone',
    async handler() {
      const node = editor.registry.create(context.name, editor);
      const data = {...context.dump(), id: node.id};

      node.load(data);

      await editor.addNode(node);
      await area.translate(node.id, {x: context.position.x + 25, y: context.position.y + 25});
    },
  };

  const list = [deleteItem];

  if (context instanceof BaseNode) {
    list.push(cloneItem);
  }

  return {
    searchBar: false,
    list,
  };
}

export class CustomContextMenuPlugin extends ContextMenuPlugin {
  constructor(menuItems) {
    super({items: (context, plugin) => contextMenuItems(menuItems, context, plugin)});
  }
}
