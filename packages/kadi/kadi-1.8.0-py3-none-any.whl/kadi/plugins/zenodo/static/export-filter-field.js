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

kadi.app.component('ExportFilterField', {
  props: {
    field: Object,
    resourceType: String,
    exportType: {
      type: String,
      default: null,
    },
    extras: {
      type: Array,
      default: () => [],
    },
  },
  data() {
    return {
      filter: {},
      isCollapsed: true,
    };
  },
  template: `
    <div class="form-group">
      <collapse-item :id="field.id"
                     class="text-default d-inline-block"
                     :is-collapsed="true"
                     :class="{'mb-2': !isCollapsed}"
                     @collapse="isCollapsed = $event">
        {$ field.label $}
      </collapse-item>
      <resource-export-filter :id="field.id"
                              :resource-type="resourceType"
                              :export-type="exportType"
                              :initial-filter="field.data"
                              :extras="extras"
                              @filter="filter = $event">
      </resource-export-filter>
      <small class="form-text text-muted">{$ field.description $}</small>
      <input type="hidden" :name="field.name" :value="JSON.stringify(filter)">
    </div>
  `,
});
