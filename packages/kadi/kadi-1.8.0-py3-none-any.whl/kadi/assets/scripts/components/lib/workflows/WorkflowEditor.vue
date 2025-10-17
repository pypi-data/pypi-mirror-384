<!-- Copyright 2020 Karlsruhe Institute of Technology
   -
   - Licensed under the Apache License, Version 2.0 (the "License");
   - you may not use this file except in compliance with the License.
   - You may obtain a copy of the License at
   -
   -     http://www.apache.org/licenses/LICENSE-2.0
   -
   - Unless required by applicable law or agreed to in writing, software
   - distributed under the License is distributed on an "AS IS" BASIS,
   - WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   - See the License for the specific language governing permissions and
   - limitations under the License. -->

<template>
  <div ref="container">
    <confirm-dialog ref="confirmDialog"></confirm-dialog>
    <tool-dialog v-if="toolsEndpoint" ref="toolDialog" :endpoint="toolsEndpoint" @add-tool="addTool"></tool-dialog>
    <variable-editor ref="variableEditor" @set-variables="setVariables"></variable-editor>
    <div ref="toolbar" class="card toolbar">
      <div class="card-body px-1 py-0">
        <button v-if="editable"
                type="button"
                title="Edit variables"
                :class="toolbarBtnClasses"
                :disabled="!initialized"
                @click="editVariables">
          <i class="fa-solid fa-table-list"></i>
        </button>
        <button v-if="editable"
                type="button"
                title="Arrange nodes"
                :class="toolbarBtnClasses"
                :disabled="!initialized"
                @click="arrangeNodes">
          <i class="fa-solid fa-diagram-project"></i>
        </button>
        <button type="button"
                title="Reset view"
                :class="toolbarBtnClasses"
                :disabled="!initialized"
                @click="resetView">
          <i class="fa-solid fa-eye"></i>
        </button>
        <button type="button"
                title="Toggle fullscreen"
                :class="toolbarBtnClasses"
                :disabled="!initialized"
                @click="toggleFullscreen">
          <i class="fa-solid fa-expand"></i>
        </button>
        <button v-if="editable"
                type="button"
                title="Clear editor"
                :class="toolbarBtnClasses"
                :disabled="!initialized"
                @click="clearEditor">
          <i class="fa-solid fa-broom"></i>
        </button>
        <i v-if="!initialized" class="fa-solid fa-circle-notch fa-spin text-muted mx-3"></i>
      </div>
    </div>
    <div class="card editor-container" :class="{'bg-light': !editable}">
      <div ref="editor"></div>
    </div>
    <slot :editor="editor"></slot>
  </div>
</template>

<style lang="scss" scoped>
.editor-container {
  border: 1px solid #ced4da;
  border-radius: 0;
}

.toolbar {
  border-bottom-left-radius: 0;
  border-bottom-right-radius: 0;
  border-color: #ced4da;
  margin-bottom: -1px;
}
</style>

<script>
import {AreaExtensions} from 'rete-area-plugin';

import {
  CustomAreaPlugin,
  CustomConnectionPlugin,
  CustomContextMenuPlugin,
  CustomRenderPlugin,
} from 'scripts/lib/workflows/plugins.js';
import {NodeBlueprint, NodeRegistry} from 'scripts/lib/workflows/core.js';
import {ToolNode} from 'scripts/lib/workflows/nodes.js';
import WorkflowEditor from 'scripts/lib/workflows/editor.js';

import annotationBlueprints from 'scripts/lib/workflows/blueprints/annotation.js';
import controlBlueprints from 'scripts/lib/workflows/blueprints/control.js';
import fileIoBlueprints from 'scripts/lib/workflows/blueprints/file-io.js';
import miscBlueprints from 'scripts/lib/workflows/blueprints/misc.js';
import sourceBlueprints from 'scripts/lib/workflows/blueprints/source.js';
import userInputBlueprints from 'scripts/lib/workflows/blueprints/user-input.js';
import userOutputBlueprints from 'scripts/lib/workflows/blueprints/user-output.js';

import ToolDialog from 'scripts/components/lib/workflows/ToolDialog.vue';
import VariableEditor from 'scripts/components/lib/workflows/VariableEditor.vue';

export default {
  components: {
    ToolDialog,
    VariableEditor,
  },
  props: {
    editable: {
      type: Boolean,
      default: true,
    },
    workflowUrl: {
      type: String,
      default: null,
    },
    toolsEndpoint: {
      type: String,
      default: null,
    },
    unsavedChanges: {
      type: Boolean,
      default: false,
    },
    isRendered: {
      type: Boolean,
      default: true,
    },
  },
  emits: ['unsaved-changes'],
  data() {
    return {
      editor: null,
      area: null,
      arrange: null,
      registry: null,
      initialized: false,
      unsavedChanges_: false,
    };
  },
  computed: {
    toolbarBtnClasses() {
      return 'btn btn-link text-primary my-1';
    },
  },
  watch: {
    workflowUrl() {
      this.loadWorkflow(this.workflowUrl);
    },
    unsavedChanges() {
      this.unsavedChanges_ = this.unsavedChanges;
    },
    unsavedChanges_() {
      this.$emit('unsaved-changes', this.unsavedChanges_);
    },
    isRendered() {
      this.resizeView(false);
    },
  },
  async mounted() {
    const onChange = () => {
      if (this.initialized) {
        this.unsavedChanges_ = true;
      }
    };

    this.registry = new NodeRegistry();
    this.area = new CustomAreaPlugin(this.$refs.editor, this.editable, onChange);
    this.editor = new WorkflowEditor(this.registry, this.area, onChange);

    const blueprints = {};

    for (const blueprint of [
      ...sourceBlueprints,
      ...controlBlueprints,
      ...userInputBlueprints,
      ...userOutputBlueprints,
      ...fileIoBlueprints,
      ...miscBlueprints,
      ...annotationBlueprints,
    ]) {
      this.registry.register(blueprint);

      const name = blueprint.name;
      const group = blueprint.type.group;

      if (!(group in blueprints)) {
        blueprints[group] = [];
      }

      blueprints[group].push({
        key: name,
        label: name,
        handler: () => this.addNode(name),
      });
    }

    const menuItems = [];

    if (this.toolsEndpoint) {
      menuItems.push({
        key: 'tools',
        label: 'Select tools...',
        class: 'font-italic',
        handler: () => this.$refs.toolDialog.open(),
      });
    }

    for (const [key, value] of Object.entries(blueprints)) {
      menuItems.push({label: key, key, handler: () => null, subitems: value});
    }

    if (kadi.globals.environment === 'development') {
      menuItems.push({
        key: 'dump',
        label: 'Dump JSON',
        class: 'font-italic',
        handler: () => console.debug(JSON.stringify(this.editor.dump(), null, 2)),
      });
    };

    const contextMenu = new CustomContextMenuPlugin(menuItems);
    const connection = new CustomConnectionPlugin();
    const render = new CustomRenderPlugin();

    this.editor.use(this.area);
    this.area.use(contextMenu);
    this.area.use(connection);
    this.area.use(render);

    this.resizeView();

    if (this.workflowUrl) {
      await this.loadWorkflow(this.workflowUrl);
    }

    this.initialized = true;

    // Disable most interactions if the editor is not editable.
    if (!this.editable) {
      const clickHandler = (e) => {
        e.preventDefault();
        e.stopPropagation();
      };

      for (const event of ['click', 'dblclick']) {
        this.$refs.editor.addEventListener(event, clickHandler, {capture: true});
      }

      const dragHandler = (e) => {
        // Always allow moving the viewport.
        if (e.target !== this.$refs.editor) {
          e.preventDefault();
          e.stopPropagation();
        }
      };

      for (const event of ['pointerdown', 'pointerup']) {
        this.$refs.editor.addEventListener(event, dragHandler, {capture: true});
      }
    }

    window.addEventListener('resize', this.resizeView);
    window.addEventListener('fullscreenchange', this.resizeView);
    window.addEventListener('beforeunload', this.beforeUnload);
  },
  unmounted() {
    window.removeEventListener('resize', this.resizeView);
    window.removeEventListener('fullscreenchange', this.resizeView);
    window.removeEventListener('beforeunload', this.beforeUnload);

    this.area.destroy();
  },
  methods: {
    resizeView(resetView = true) {
      if (!this.isRendered) {
        return;
      }

      const toolbar = this.$refs.toolbar;
      const editor = this.$refs.editor;

      if (kadi.utils.isFullscreen()) {
        const toolbarHeight = Math.round(toolbar.getBoundingClientRect().height);

        editor.style.height = `calc(100vh - ${toolbarHeight - 1}px)`;
        toolbar.style.borderTopLeftRadius = toolbar.style.borderTopRightRadius = '0';
      } else {
        const containerWidth = Math.round(editor.getBoundingClientRect().width);
        const containerHeight = Math.round(window.innerHeight / window.innerWidth * containerWidth);

        editor.style.height = `${containerHeight}px`;
        toolbar.style.borderTopLeftRadius = toolbar.style.borderTopRightRadius = '0.25rem';
      }

      if (resetView) {
        this.resetView();
      }
    },
    setVariables(variables) {
      this.editor.setVariables(variables);

      if (this.initialized) {
        this.unsavedChanges_ = true;
      }
    },
    editVariables() {
      this.$refs.variableEditor.open();
    },
    async arrangeNodes() {
      const input = await this.$refs.confirmDialog.open('Are you sure you want to rearrange all nodes?');

      if (!input.status) {
        return;
      }

      // eslint-disable-next-line @stylistic/js/function-paren-newline
      const mod = await import(
        /* webpackChunkName: "workflow-arrange" */
        'rete-auto-arrange-plugin');

      class CustomArrangeApplier extends mod.ArrangeAppliers.StandardApplier {
        async resizeNode() {
          // Do nothing.
        }
      };

      if (!this.arrange) {
        this.arrange = new mod.AutoArrangePlugin();
        this.arrange.addPreset(mod.Presets.classic.setup());
        this.area.use(this.arrange);
      }

      await this.arrange.layout({applier: new CustomArrangeApplier()});

      this.resetView();
    },
    resetView() {
      AreaExtensions.zoomAt(this.area, this.editor.getNodes());
    },
    toggleFullscreen() {
      kadi.utils.toggleFullscreen(this.$refs.container);
    },
    async clearEditor() {
      const input = await this.$refs.confirmDialog.open('Are you sure you want to clear the editor?');

      if (!input.status) {
        return;
      }

      await this.editor.clear();

      this.unsavedChanges_ = false;
    },
    async loadWorkflow(url) {
      try {
        const response = await axios.get(url);

        try {
          await this.editor.load(response.data, this.registry);
          this.$refs.variableEditor.setVariables(this.editor.variables);
        } catch (error) {
          console.error(error);
          kadi.base.flashDanger('Error parsing workflow data.');
        } finally {
          this.resetView();
        }
      } catch (error) {
        kadi.base.flashDanger('Error loading workflow.', error.request);
      }
    },
    async addTool(tool) {
      const name = ToolNode.nameFromTool(tool);

      if (!this.registry.has(name)) {
        const blueprint = new NodeBlueprint(ToolNode, name, tool);
        this.registry.register(blueprint);
      }

      await this.addNode(name);
    },
    async addNode(name) {
      const node = this.registry.create(name, this.editor);

      await this.editor.addNode(node);
      await this.area.translate(node.id, this.area.clickPosition);
    },
    beforeUnload(e) {
      if (this.unsavedChanges_) {
        e.preventDefault();
        return '';
      }
      return null;
    },
  },
};
</script>
