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

<template>
  <div>
    <div v-if="fileSize > maxFileSize && !forceLoad">
      <button type="button" class="btn btn-sm btn-light mb-2" @click="loadFile">
        <i class="fa-solid fa-eye"></i> {{ $t('Load preview') }}
      </button>
    </div>
    <div v-else ref="container">
      <div ref="toolbar" class="card toolbar">
        <div class="card-body px-1 py-0">
          <button type="button"
                  :class="toolbarBtnClasses"
                  :disabled="loading"
                  :title="$t('Toggle wireframe')"
                  @click="toggleWireframe">
            <i class="fa-solid fa-cube"></i>
          </button>
          <button type="button"
                  :class="toolbarBtnClasses"
                  :disabled="loading"
                  :title="$t('Reset view')"
                  @click="resetView">
            <i class="fa-solid fa-eye"></i>
          </button>
          <button type="button"
                  :class="toolbarBtnClasses"
                  :disabled="loading"
                  :title="$t('Toggle fullscreen')"
                  @click="toggleFullscreen">
            <i class="fa-solid fa-expand"></i>
          </button>
          <input v-model.number="opacity"
                 type="range"
                 class="align-middle mx-3"
                 :disabled="loading"
                 :title="$t('Opacity')">
          <div v-if="colorByOptions.length > 1"
               class="input-group input-group-sm d-md-inline-flex w-auto my-1 mr-0 mr-md-2">
            <div class="input-group-prepend">
              <span class="input-group-text">{{ $t('Field data') }}</span>
            </div>
            <select v-model="selectedColor" class="custom-select">
              <option v-for="option in colorByOptions" :key="option.value" :value="option.value">
                {{ option.label }}
              </option>
            </select>
          </div>
          <div v-if="componentOptions.length > 0"
               class="input-group input-group-sm d-md-inline-flex w-auto my-1">
            <div class="input-group-prepend">
              <span class="input-group-text">{{ $t('Components') }}</span>
            </div>
            <select v-model="selectedComponent" class="custom-select">
              <option v-for="option in componentOptions" :key="option.value" :value="option.value">
                {{ option.label }}
              </option>
            </select>
          </div>
        </div>
      </div>
      <div ref="renderContainer" class="render-container bg-light">
        <div v-if="error" class="text-muted ml-3 my-2">
          <i class="fa-solid fa-triangle-exclamation mr-1"></i> {{ error }}
        </div>
        <div v-else-if="loading" class="text-muted ml-3 my-2">
          <i class="fa-solid fa-circle-notch fa-spin mr-1"></i> {{ $t('Loading model...') }}
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.render-container {
  border: 1px solid #ced4da;
  cursor: pointer;
}

.toolbar {
  border-bottom-left-radius: 0;
  border-bottom-right-radius: 0;
  border-color: #ced4da;
  margin-bottom: -1px;
}
</style>

<script>
import '@kitware/vtk.js/Rendering/Profiles/Geometry';
import {ColorMode, ScalarMode} from '@kitware/vtk.js/Rendering/Core/Mapper/Constants';
import HttpDataAccessHelper from '@kitware/vtk.js/IO/Core/DataAccessHelper/HttpDataAccessHelper';
import WebGLUtil from 'three/examples/jsm/capabilities/WebGL.js';
import vtkActor from '@kitware/vtk.js/Rendering/Core/Actor';
import vtkColorMaps from '@kitware/vtk.js/Rendering/Core/ColorTransferFunction/ColorMaps';
import vtkColorTransferFunction from '@kitware/vtk.js/Rendering/Core/ColorTransferFunction';
import vtkFullScreenRenderWindow from '@kitware/vtk.js/Rendering/Misc/FullScreenRenderWindow';
import vtkMapper from '@kitware/vtk.js/Rendering/Core/Mapper';
import vtkScalarBarActor from '@kitware/vtk.js/Rendering/Core/ScalarBarActor';
import vtkXMLPolyDataReader from '@kitware/vtk.js/IO/XML/XMLPolyDataReader';

export default {
  props: {
    url: String,
    fileSize: Number,
    maxFileSize: Number,
  },
  data() {
    return {
      outputData: null,
      fullScreenRenderWindow: null,
      modelActor: null,
      scalarBarActor: null,
      activeArray: null,
      cameraPosition: null,
      cameraViewUp: null,
      colorByOptions: [],
      selectedColor: null,
      componentOptions: [],
      selectedComponent: null,
      opacity: 100,
      loading: true,
      forceLoad: false,
      error: '',
    };
  },
  computed: {
    toolbarBtnClasses() {
      return 'btn btn-link text-primary my-1';
    },
  },
  watch: {
    selectedColor() {
      this.updateColorBy();
    },
    selectedComponent() {
      this.updateColorByComponent();
    },
    opacity() {
      this.modelActor.getProperty().setOpacity(this.opacity / 100);
      this.renderView();
    },
  },
  mounted() {
    if (!WebGLUtil.isWebGL2Available()) {
      this.error = $t('WebGL not available.');
      return;
    }

    if (this.fileSize <= this.maxFileSize) {
      this.loadFile();
    }
  },
  unmounted() {
    window.removeEventListener('resize', this.resizeView);
    window.removeEventListener('fullscreenchange', this.resizeView);
  },
  methods: {
    toggleWireframe() {
      const property = this.modelActor.getProperty();
      const representation = property.getRepresentation() === 2 ? 1 : 2;
      const edgeVisibility = property.getEdgeVisibility();

      property.set({representation, edgeVisibility});
      this.renderView();
    },
    resetView() {
      const renderer = this.fullScreenRenderWindow.getRenderer();
      const camera = renderer.getActiveCamera();

      camera.setPosition(...this.cameraPosition);
      camera.setViewUp(...this.cameraViewUp);
      renderer.resetCamera();

      this.renderView();
    },
    toggleFullscreen() {
      kadi.utils.toggleFullscreen(this.$refs.container);
    },
    resizeView() {
      const toolbar = this.$refs.toolbar;
      const renderContainer = this.$refs.renderContainer;

      if (kadi.utils.isFullscreen()) {
        const toolbarHeight = Math.round(toolbar.getBoundingClientRect().height);

        renderContainer.style.height = `calc(100vh - ${toolbarHeight - 1}px)`;
        toolbar.style.borderTopLeftRadius = toolbar.style.borderTopRightRadius = '0';
      } else {
        const containerWidth = Math.round(renderContainer.getBoundingClientRect().width);
        const containerHeight = Math.round(window.innerHeight / window.innerWidth * containerWidth);

        renderContainer.style.height = `${containerHeight}px`;
        toolbar.style.borderTopLeftRadius = toolbar.style.borderTopRightRadius = '0.25rem';
      }

      this.fullScreenRenderWindow.resize();
    },
    renderView() {
      const renderWindow = this.fullScreenRenderWindow.getRenderWindow();
      renderWindow.render();
    },
    updateColorBy() {
      const mapper = this.modelActor.getMapper();
      const [fieldType, colorByArrayName] = this.selectedColor.split(':');
      const showFieldData = fieldType.length > 0;
      const isPointData = fieldType === 'PointData';

      let colorMode = ColorMode.DEFAULT;
      let scalarMode = ScalarMode.DEFAULT;

      this.componentOptions = [];

      if (showFieldData) {
        const lookupTable = mapper.getLookupTable();

        colorMode = ColorMode.MAP_SCALARS;
        scalarMode = isPointData ? ScalarMode.USE_POINT_FIELD_DATA : ScalarMode.USE_CELL_FIELD_DATA;

        this.activeArray = this.outputData[`get${fieldType}`]().getArrayByName(colorByArrayName);
        const numberOfComponents = this.activeArray.getNumberOfComponents();

        if (numberOfComponents > 1) {
          lookupTable.setVectorModeToMagnitude();

          // Initialize the options for the component selection.
          this.componentOptions = [{value: -1, label: $t('Magnitude')}];
          this.selectedComponent = -1;

          for (let i = 0; i < numberOfComponents; i++) {
            this.componentOptions.push({value: i, label: `${$t('Component')} ${i + 1}`});
          }
          if (numberOfComponents === 3 || numberOfComponents === 4) {
            this.componentOptions.push({value: -2, label: $t('Direct mapping')});
          }
        }

        this.scalarBarActor.setAxisLabel(colorByArrayName);
        this.scalarBarActor.setVisibility(true);

        const preset = vtkColorMaps.getPresetByName('jet');
        const dataRange = this.activeArray.getRange();

        lookupTable.applyColorMap(preset);
        lookupTable.setMappingRange(dataRange[0], dataRange[1]);
        lookupTable.updateRange();
      } else {
        this.scalarBarActor.setVisibility(false);
      }

      mapper.set({
        colorByArrayName,
        colorMode,
        interpolateScalarsBeforeMapping: isPointData,
        scalarMode,
        scalarVisibility: showFieldData,
      });

      this.renderView();
    },
    updateColorByComponent() {
      const mapper = this.modelActor.getMapper();
      mapper.setColorModeToMapScalars();

      const lookupTable = mapper.getLookupTable();
      const selectedComponent = Number(this.selectedComponent);
      const dataRange = this.activeArray.getRange(selectedComponent);

      if (selectedComponent === -2) {
        mapper.setColorModeToDirectScalars();
      } else if (selectedComponent === -1) {
        lookupTable.setVectorModeToMagnitude();
        lookupTable.setMappingRange(dataRange[0], dataRange[1]);
        lookupTable.updateRange();
      } else {
        lookupTable.setVectorModeToComponent();
        lookupTable.setVectorComponent(selectedComponent);
        lookupTable.setMappingRange(dataRange[0], dataRange[1]);
        lookupTable.updateRange();
      }

      this.renderView();
    },
    initializeViewer() {
      // Initialize the options for the field data selection.
      this.colorByOptions.push({label: '', value: ':'});

      for (const pointDataArray of this.outputData.getPointData().getArrays()) {
        this.colorByOptions.push({
          label: `(p) ${pointDataArray.getName()}`,
          value: `PointData:${pointDataArray.getName()}`,
        });
      }

      for (const cellDataArray of this.outputData.getCellData().getArrays()) {
        this.colorByOptions.push({
          label: `(c) ${cellDataArray.getName()}`,
          value: `CellData:${cellDataArray.getName()}`,
        });
      }

      this.selectedColor = this.colorByOptions[0].value;

      // Initialize all rendering components.
      const bgColor = 0.9686274509803922;
      this.fullScreenRenderWindow = vtkFullScreenRenderWindow.newInstance({
        background: [bgColor, bgColor, bgColor],
        containerStyle: {height: '100%', width: '100%'},
        rootContainer: this.$refs.renderContainer,
      });

      const lookupTable = vtkColorTransferFunction.newInstance();
      const mapper = vtkMapper.newInstance({
        interpolateScalarsBeforeMapping: false,
        lookupTable,
        scalarVisibility: false,
        useLookupTableScalarRange: true,
      });
      mapper.setInputData(this.outputData);

      this.modelActor = vtkActor.newInstance();
      this.modelActor.setMapper(mapper);
      this.modelActor.getProperty().setColor([0.8, 0.8, 0.8]);

      this.scalarBarActor = vtkScalarBarActor.newInstance();
      this.scalarBarActor.setScalarsToColors(lookupTable);
      this.scalarBarActor.setVisibility(false);

      const fontStyle = {fontFamily: 'Arial, sans-serif', fontColor: 'black'};
      this.scalarBarActor.setAxisTextStyle(fontStyle);
      this.scalarBarActor.setTickTextStyle(fontStyle);

      const renderer = this.fullScreenRenderWindow.getRenderer();
      renderer.addActor(this.modelActor);
      renderer.addActor(this.scalarBarActor);
      renderer.resetCamera();

      const camera = renderer.getActiveCamera();
      this.cameraPosition = camera.getPosition();
      this.cameraViewUp = camera.getViewUp();

      const renderWindow = this.fullScreenRenderWindow.getRenderWindow();
      renderWindow.getInteractor().setDesiredUpdateRate(15);

      this.renderView();
    },
    async loadFile() {
      this.forceLoad = true;

      await this.$nextTick();

      try {
        const data = await HttpDataAccessHelper.fetchBinary(this.url);
        const vtpReader = vtkXMLPolyDataReader.newInstance();
        vtpReader.parseAsArrayBuffer(data);

        this.outputData = vtpReader.getOutputData(0);
        this.initializeViewer();
      } catch (error) {
        this.error = $t('Error loading model.');
        console.error(error);
        return;
      }

      this.resizeView();
      this.loading = false;

      window.addEventListener('resize', this.resizeView);
      window.addEventListener('fullscreenchange', this.resizeView);
    },
  },
};
</script>
