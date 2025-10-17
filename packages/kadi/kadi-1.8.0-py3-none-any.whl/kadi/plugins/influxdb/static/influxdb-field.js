/* Copyright 2022 Karlsruhe Institute of Technology
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

kadi.app.component('InfluxdbField', {
  props: {
    field: Object,
    influxdbs: Object,
  },
  data() {
    return {
      preferences: [],
    };
  },
  computed: {
    serializedPreferences() {
      // Ignore instances without a (non empty) token.
      return JSON.stringify(this.preferences.filter((config) => config.token));
    },
  },
  mounted() {
    this.preferences = kadi.utils.deepClone(this.field.data);

    // Merge available and configured DBs.
    const configuredDbs = new Set(this.preferences.map((config) => config.name));

    Object.entries(this.influxdbs).forEach(([name, config]) => {
      if (!configuredDbs.has(name)) {
        this.preferences.push({name, token: '', title: config.title});
      }
    });

    this.preferences.sort((a, b) => ((a.title > b.title) ? 1 : ((b.title > a.title) ? -1 : 0)));
  },
  template: `
    <div>
      <ul class="list-group mb-3">
        <li class="list-group-item py-2 bg-light">
          <div class="row">
            <div class="col-md-6">{$ $t('Name') $}</div>
            <div class="col-md-6">{$ $t('Token') $}</div>
          </div>
        </li>
        <li class="list-group-item" v-for="preference in preferences" :key="preference.name">
          <div class="row align-items-center">
            <div class="col-md-6 mb-2 mb-md-0">{$ preference.title $}</div>
            <div class="col-md-6 mb-2 mb-md-0">
              <span v-if="!influxdbs[preference.name] || !influxdbs[preference.name].has_token">
                <input class="form-control form-control-sm" type="password" v-model="preference.token"/>
              </span>
              <span v-else>
                <em>{$ $t('Configured globally') $}</em>
              </span>
            </div>
          </div>
          <div class="mt-1">
            <small class="text-danger" v-if="!influxdbs[preference.name]">
              <i class="fa-solid fa-triangle-exclamation"></i> {$ $t('Database disabled or no access rights.') $}
            </small>
            <small class="text-muted" v-else>
              <i class="fa-solid fa-circle-info"></i>
              <strong>{$ $t('Query endpoint:') $}</strong> {$ influxdbs[preference.name].query_endpoint $}
            </small>
          </div>
        </li>
      </ul>
      <input type="hidden" :name="field.name" :value="serializedPreferences">
    </div>
  `,
});
