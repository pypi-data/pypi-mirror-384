<!-- Copyright 2021 Karlsruhe Institute of Technology
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

<script setup>
import {onBeforeMount, onMounted, onUnmounted, ref, useTemplateRef, watch} from 'vue';

import {useResourceGraph} from 'scripts/components/composables/resource-graph.js';

const props = defineProps({
  endpoint: String,
  startRecord: Number,
  initialDepth: {
    type: Number,
    default: 1,
  },
  isRendered: {
    type: Boolean,
    default: true,
  },
});

const emit = defineEmits(['update-depth']);

const containerRef = useTemplateRef('container-ref');
const toolbarRef = useTemplateRef('toolbar-ref');
const graphRef = useTemplateRef('graph-ref');

const depth = ref(null);
const direction = ref('');
const initialized = ref(false);
const loading = ref(true);

let nodes = [];
let links = [];

let nodesContainer = null;
let linksContainer = null;
let updateTimeoutHandle = null;

const suffix = kadi.utils.randomAlnum();
const toolbarBtnClasses = 'btn btn-link text-primary my-1';
const minDepth = 1;
const maxDepth = 3;

function getStartNode() {
  return nodes.find((node) => node.id === props.startRecord) || null;
}

const {
  filter,
  forceDisabled,
  legendHidden,
  labelsHidden,
  downloadGraph,
  resizeView,
  resetView,
  createContainers,
  createSimulation,
  drawGraph,
} = useResourceGraph(suffix, getStartNode);

function resizeCallback() {
  resizeView(containerRef.value, toolbarRef.value, props.isRendered);
  resetView();
}

function toggleFullscreen() {
  kadi.utils.toggleFullscreen(containerRef.value);
}

async function updateData() {
  loading.value = true;

  try {
    const params = {depth: depth.value, direction: direction.value};
    const response = await axios.get(props.endpoint, {params});

    const data = response.data;
    const prevStartNode = getStartNode();

    nodes = data.records;
    links = data.record_links;

    for (const node of nodes) {
      node._type = 'record';
    }

    // Give the start node a fixed position based on its previous position or use the origin as fallback.
    const startNode = getStartNode();

    if (startNode) {
      startNode.fx = prevStartNode ? prevStartNode.x : 0;
      startNode.fy = prevStartNode ? prevStartNode.y : 0;
    }

    // For simplicity, we just remove the existing nodes and links each time.
    nodesContainer.selectAll('*').remove();
    linksContainer.selectAll('*').remove();

    drawGraph(nodes, links);
  } catch (error) {
    kadi.base.flashDanger($t('Error loading record links.'), error.request);
  } finally {
    initialized.value = true;
    loading.value = false;
    forceDisabled.value = false;
  }
}

watch(depth, () => {
  if (initialized.value) {
    window.clearTimeout(updateTimeoutHandle);
    updateTimeoutHandle = window.setTimeout(updateData, 500);

    emit('update-depth', depth.value);
  }
});
watch(direction, updateData);
watch(() => props.isRendered, () => {
  resizeView(containerRef.value, toolbarRef.value, props.isRendered);
});

onBeforeMount(() => {
  depth.value = kadi.utils.clamp(props.initialDepth, minDepth, maxDepth);
});

onMounted(() => {
  [nodesContainer, linksContainer] = createContainers(graphRef.value);
  createSimulation();

  resizeCallback();
  updateData();

  window.addEventListener('resize', resizeCallback);
  window.addEventListener('fullscreenchange', resizeCallback);
});

onUnmounted(() => {
  window.removeEventListener('resize', resizeCallback);
  window.removeEventListener('fullscreenchange', resizeCallback);
});
</script>

<template>
  <div ref="container-ref">
    <div ref="toolbar-ref" class="card toolbar">
      <div class="card-body px-1 py-0">
        <div class="form-row align-items-center">
          <div class="col-lg-6">
            <button type="button"
                    :title="$t('Toggle forces')"
                    :class="toolbarBtnClasses + (forceDisabled ? ' border-active' : '')"
                    :disabled="!initialized"
                    @click="forceDisabled = !forceDisabled">
              <i class="fa-solid fa-thumbtack"></i>
            </button>
            <button type="button"
                    :title="$t('Toggle legend')"
                    :class="toolbarBtnClasses + (legendHidden ? ' border-active' : '')"
                    :disabled="!initialized"
                    @click="legendHidden = !legendHidden">
              <i class="fa-solid fa-tags"></i>
            </button>
            <button type="button"
                    :title="$t('Toggle labels')"
                    :class="toolbarBtnClasses + (labelsHidden ? ' border-active' : '')"
                    :disabled="!initialized"
                    @click="labelsHidden = !labelsHidden">
              <i class="fa-solid fa-font"></i>
            </button>
            <button type="button"
                    :title="$t('Download graph')"
                    :class="toolbarBtnClasses"
                    :disabled="!initialized"
                    @click="downloadGraph">
              <i class="fa-solid fa-download"></i>
            </button>
            <button type="button"
                    :title="$t('Reset view')"
                    :class="toolbarBtnClasses"
                    :disabled="!initialized"
                    @click="resetView">
              <i class="fa-solid fa-eye"></i>
            </button>
            <button type="button"
                    :title="$t('Toggle fullscreen')"
                    :class="toolbarBtnClasses"
                    :disabled="!initialized"
                    @click="toggleFullscreen">
              <i class="fa-solid fa-expand"></i>
            </button>
            <div class="d-inline-block">
              <button type="button"
                      :title="$t('Decrease link depth')"
                      :class="toolbarBtnClasses"
                      :disabled="!initialized || depth <= minDepth"
                      @click="depth--">
                <i class="fa-solid fa-angle-left"></i>
              </button>
              <strong :class="{'text-muted': !initialized}">{{ $t('Link depth') }}: {{ depth }}</strong>
              <button type="button"
                      :title="$t('Increase link depth')"
                      :class="toolbarBtnClasses"
                      :disabled="!initialized || depth >= maxDepth"
                      @click="depth++">
                <i class="fa-solid fa-angle-right"></i>
              </button>
            </div>
            <i v-if="loading" class="fa-solid fa-circle-notch fa-spin text-muted ml-2"></i>
          </div>
          <div class="col-lg-6 mb-2 mb-lg-0">
            <div class="form-row">
              <div class="col-sm-6 mb-2 mb-sm-0">
                <select v-model="direction" class="custom-select custom-select-sm">
                  <option value="">{{ $t('All links') }}</option>
                  <option value="out">{{ $t('Outgoing links') }}</option>
                  <option value="in">{{ $t('Incoming links') }}</option>
                </select>
              </div>
              <div class="col-sm-6">
                <div class="input-group input-group-sm">
                  <input :id="`filter-${suffix}`"
                         v-model="filter"
                         class="form-control"
                         :placeholder="$t('Filter by identifier or link name')">
                  <clear-button :input="filter" :input-id="`filter-${suffix}`" @clear-input="filter = ''">
                  </clear-button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
    <div ref="graph-ref" class="card graph"></div>
  </div>
</template>

<style scoped>
.border-active {
  border: 1px solid #ced4da;
}

.graph {
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
