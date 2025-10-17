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

import {newVue} from 'scripts/lib/core.js';

import ExcelViewer from 'scripts/components/lib/previews/ExcelViewer.vue';
import ModelViewer from 'scripts/components/lib/previews/ModelViewer.vue';
import VtpViewer from 'scripts/components/lib/previews/VtpViewer.vue';
import WorkflowEditor from 'scripts/components/lib/workflows/WorkflowEditor.vue';

newVue({
  components: {
    ExcelViewer,
    ModelViewer,
    VtpViewer,
    WorkflowEditor,
  },
  data() {
    return {
      previewData: null,
      initialized: false,
    };
  },
  async mounted() {
    try {
      const response = await axios.get(kadi.context.get_file_preview_endpoint);

      this.previewData = response.data;
      this.initialized = true;
    } catch (error) {
      if (error.request.status === 404) {
        this.initialized = true;
      } else {
        kadi.base.flashDanger($t('Error loading file preview.'), error.request);
      }
    }
  },
});
