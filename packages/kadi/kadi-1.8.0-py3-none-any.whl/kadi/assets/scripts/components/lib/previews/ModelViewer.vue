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
          <button v-if="material !== null"
                  type="button"
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
import * as THREE from 'three';
import {OBJLoader} from 'three/examples/jsm/loaders/OBJLoader.js';
import {STLLoader} from 'three/examples/jsm/loaders/STLLoader.js';
import {TrackballControls} from 'three/examples/jsm/controls/TrackballControls.js';
import WebGLUtil from 'three/examples/jsm/capabilities/WebGL.js';
import {XYZLoader} from 'three/examples/jsm/loaders/XYZLoader.js';
import {markRaw} from 'vue';

export default {
  props: {
    type: String,
    modelUrl: String,
    fileSize: Number,
    maxFileSize: Number,
  },
  data() {
    return {
      loaders: {
        'obj': OBJLoader,
        'stl': STLLoader,
        'xyz': XYZLoader,
      },
      renderer: null,
      scene: null,
      camera: null,
      controls: null,
      material: null,
      distance: 0,
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
  mounted() {
    if (!(this.type in this.loaders)) {
      this.error = 'Invalid object type.';
      return;
    }

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
      this.material.wireframe = !this.material.wireframe;
    },
    resetView() {
      this.controls.reset();
      this.camera.position.set(0, 0, this.distance);
      this.camera.updateProjectionMatrix();
    },
    toggleFullscreen() {
      kadi.utils.toggleFullscreen(this.$refs.container);
    },
    resizeView() {
      const toolbar = this.$refs.toolbar;
      const container = this.$refs.container;

      const canvasWidth = Math.round(container.getBoundingClientRect().width) - 2;
      let canvasHeight = 1;

      if (kadi.utils.isFullscreen()) {
        const containerHeight = Math.round(container.getBoundingClientRect().height);
        const toolbarHeight = Math.round(toolbar.getBoundingClientRect().height);

        canvasHeight = Math.max(containerHeight - toolbarHeight - 1, canvasHeight);
        toolbar.style.borderTopLeftRadius = toolbar.style.borderTopRightRadius = '0';
      } else {
        canvasHeight = Math.round(window.innerHeight / window.innerWidth * canvasWidth);
        toolbar.style.borderTopLeftRadius = toolbar.style.borderTopRightRadius = '0.25rem';
      }

      this.camera.aspect = canvasWidth / canvasHeight;
      this.camera.updateProjectionMatrix();
      this.renderer.setSize(canvasWidth, canvasHeight);
    },
    animate() {
      window.requestAnimationFrame(this.animate);
      this.renderer.render(this.scene, this.camera);
      this.controls.update();
    },
    onLoad(data) {
      this.renderer = new THREE.WebGLRenderer({antialias: true});
      this.renderer.setPixelRatio(window.devicePixelRatio);
      this.$refs.renderContainer.appendChild(this.renderer.domElement);

      // Prevent Vue from making this object reactive, as Three.js uses similar mechanisms internally.
      this.scene = markRaw(new THREE.Scene());
      this.scene.background = new THREE.Color(0xf7f7f7);

      this.camera = new THREE.PerspectiveCamera();
      this.scene.add(this.camera);

      this.controls = new TrackballControls(this.camera, this.renderer.domElement);
      this.controls.staticMoving = true;

      let object = null;

      switch (this.type) {
        case 'obj':
          this.material = new THREE.MeshNormalMaterial();
          object = data;

          object.traverse((child) => {
            if (child instanceof THREE.Mesh) {
              child.material = this.material;
            }
          });
          break;

        case 'stl':
          this.material = new THREE.MeshNormalMaterial();
          object = new THREE.Mesh(data, this.material);
          object.geometry.center();
          break;

        case 'xyz':
          object = new THREE.Points(data, new THREE.PointsMaterial({size: 0.1, color: 0}));
          break;

        default:
          return;
      }

      this.scene.add(object);

      // Calculate a good default distance along the z-axis for the camera relative to the size of the object.
      const boundingBox = new THREE.Box3().setFromObject(object);
      const length = boundingBox.getSize(new THREE.Vector3()).length();
      const fov = this.camera.fov / 2 * (Math.PI / 180);

      this.distance = length / 2 / Math.tan(fov);

      // Check if the object would be even visible using the calculated distance. If not, attempt to calculate a new
      // distance where at least part of the object should be visible.
      if (this.distance - this.camera.far > boundingBox.max.z) {
        this.distance = this.camera.far + boundingBox.max.z - (boundingBox.max.z / 10);
      }

      this.resizeView();
      this.resetView();
      this.animate();

      this.loading = false;

      window.addEventListener('resize', this.resizeView);
      window.addEventListener('fullscreenchange', this.resizeView);
    },
    onError(error) {
      this.error = $t('Error loading model.');
      console.error(error);
    },
    async loadFile() {
      this.forceLoad = true;

      await this.$nextTick();

      const loader = new this.loaders[this.type]();
      loader.load(this.modelUrl, this.onLoad, null, this.onError);
    },
  },
};
</script>
