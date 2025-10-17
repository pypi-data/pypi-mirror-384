<!-- Copyright 2023 Karlsruhe Institute of Technology
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
import {onMounted, onUnmounted, ref, useTemplateRef, watch} from 'vue';

import * as d3 from 'd3';

import {useResourceGraph} from 'scripts/components/composables/resource-graph.js';

const props = defineProps({
  endpoint: String,
  isRendered: {
    type: Boolean,
    default: true,
  },
});

const containerRef = useTemplateRef('container-ref');
const toolbarRef = useTemplateRef('toolbar-ref');
const graphRef = useTemplateRef('graph-ref');

const initialized = ref(false);
const loading = ref(true);

let data = null;
let simulation = null;

const nodes = [];
const links = [];
const excludedRecords = [];
const excludedCollections = [];

const suffix = kadi.utils.randomAlnum();
const toolbarBtnClasses = 'btn btn-link text-primary my-1';
const coordinateStrength = 0.1;

function getStartNode() {
  return nodes.find((node) => node.id === data.id) || null;
}

const {
  filter,
  forceDisabled,
  legendHidden,
  labelsHidden,
  createContainers,
  createSimulation,
  drawGraph,
  downloadGraph,
  resizeView,
  resetView,
  filterNodes,
} = useResourceGraph(
  suffix,
  getStartNode,
  () => {
    simulation.force('x').strength(coordinateStrength);
    simulation.force('y').strength(coordinateStrength);
  },
  () => {
    simulation.force('x').strength(0);
    simulation.force('y').strength(0);
  },
);

function resizeCallback() {
  resizeView(containerRef.value, toolbarRef.value, props.isRendered);
  resetView();
}

function toggleFullscreen() {
  kadi.utils.toggleFullscreen(containerRef.value);
}

function updateRecordNodes(collection) {
  for (const record of collection.records) {
    nodes.push({...record, collection: collection.id, _type: 'record'});
  }
  for (const recordLink of collection.record_links) {
    links.push({...recordLink});
  }
}

function findCollection(id, _collection = null) {
  let collection = _collection;

  if (collection === null) {
    collection = data;
  }
  if (collection.id === id) {
    return collection;
  }
  if (collection.children === null) {
    return null;
  }

  for (const child of collection.children) {
    const result = findCollection(id, child);

    if (result !== null) {
      return result;
    }
  }

  return null;
}

function iterateChildCollections(collection, callback, isCollapsed = false) {
  if (collection.children === null) {
    return;
  }

  const isCollapsed_ = isCollapsed || collection._collapsed;

  for (const child of collection.children) {
    callback(child, isCollapsed_);
    iterateChildCollections(child, callback, isCollapsed_);
  }
}

async function updateData(endpoint) {
  loading.value = true;

  try {
    const response = await axios.get(endpoint);
    const responseData = response.data;

    if (!initialized.value) {
      data = responseData;
      nodes.push({...responseData, _type: 'collection'});
      updateRecordNodes(responseData);
    } else {
      const collection = findCollection(responseData.id);

      // Initialize the records of the collection, if applicable.
      if (responseData.records !== null) {
        collection.records = responseData.records;
        collection.record_links = responseData.record_links;

        updateRecordNodes(collection);
      }

      // Initialize the children of the collection, if applicable.
      if (responseData.children !== null) {
        collection.children = responseData.children;

        for (const child of collection.children) {
          child.parent = collection;

          nodes.push({...child, _type: 'collection'});
          links.push({
            id: `${collection.id}-${child.id}`,
            source: collection.id,
            target: child.id,
          });
        }
      }
    }

    // eslint-disable-next-line no-use-before-define
    updateGraph();
  } catch (error) {
    kadi.base.flashDanger($t('Error loading collection links.'), error.request);
  } finally {
    initialized.value = true;
    loading.value = false;
    forceDisabled.value = false;
  }
}

function updateGraph() {
  // Determine a (new) tree layout for the collection hierarchy.
  const root = d3.hierarchy(data);

  const treeLayout = d3
    .tree()
    .nodeSize([750, 500])
    .separation(() => 1);

  treeLayout(root);

  for (const node of nodes) {
    // If the node was never moved, use the coordinates of the tree layout.
    if (node._type === 'collection' && !node._moved) {
      const treeNode = root.find((d) => d.data.id === node.id);

      node.fx = treeNode.x;
      node.fy = treeNode.y;
    }
  }

  const recordsCallback = (d) => {
    const collection = findCollection(d.id);
    collection._showRecords = !collection._showRecords;

    // Only update the data if the records are still uninitialized.
    if (collection.records === null) {
      updateData(collection.records_endpoint);
      return;
    }

    // Toggle the records.
    for (const node of nodes) {
      if (node._type === 'record' && node.collection === collection.id) {
        if (!excludedRecords.includes(node.id)) {
          excludedRecords.push(node.id);
        } else {
          kadi.utils.removeFromArray(excludedRecords, node.id);
        }
      }
    }

    filterNodes(excludedRecords);
  };

  const childrenCallback = (d) => {
    const collection = findCollection(d.id);

    // Only update the data if the children are still uninitialized.
    if (collection.children === null) {
      updateData(collection.children_endpoint);
      return;
    }

    collection._collapsed = !collection._collapsed;

    // Toggle the child collections.
    iterateChildCollections(collection, (child, isCollapsed) => {
      if (isCollapsed) {
        if (!excludedCollections.includes(child.id)) {
          excludedCollections.push(child.id);

          for (const node of nodes) {
            if (node._type === 'record' && node.collection === child.id) {
              excludedRecords.push(node.id);
            }
          }
        }
      } else {
        kadi.utils.removeFromArray(excludedCollections, child.id);

        if (child._showRecords) {
          for (const node of nodes) {
            if (node._type === 'record' && node.collection === child.id) {
              kadi.utils.removeFromArray(excludedRecords, node.id);
            }
          }
        }
      }
    });

    filterNodes(excludedRecords, excludedCollections);
  };

  drawGraph(nodes, links, true, recordsCallback, childrenCallback);
}

watch(() => props.isRendered, () => {
  resizeView(containerRef.value, toolbarRef.value, props.isRendered);
});

onMounted(() => {
  createContainers(graphRef.value);
  simulation = createSimulation();

  // Force the position of records to their collection coordinates.
  const foorceCoordinate = (d, coordinate) => {
    let result = 0;

    if (d._type === 'record') {
      const node = nodes.find((node) => node.id === d.collection);
      result = node[`f${coordinate}`];
    }

    return result || 0;
  };

  const forceX = d3
    .forceX()
    .strength(coordinateStrength)
    .x((d) => foorceCoordinate(d, 'x'));

  const forceY = d3
    .forceY()
    .strength(coordinateStrength)
    .y((d) => foorceCoordinate(d, 'y'));

  simulation.force('x', forceX).force('y', forceY);

  resizeCallback();
  updateData(props.endpoint);

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
          <div class="col-md-6">
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
            <i v-if="loading" class="fa-solid fa-circle-notch fa-spin text-muted ml-2"></i>
          </div>
          <div class="col-md-6 mb-2 mb-md-0">
            <div class="input-group input-group-sm">
              <input :id="`filter-${suffix}`"
                     v-model="filter"
                     class="form-control"
                     :placeholder="$t('Filter by identifier or link name')">
              <clear-button :input="filter" :input-id="`filter-${suffix}`" @clear-input="filter = ''"></clear-button>
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
