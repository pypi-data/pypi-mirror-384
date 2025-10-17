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
  <div>
    <div v-for="(query, index) in queries" :key="query.id">
      <div class="form-row mb-4 mb-xl-2">
        <div class="col-xl-1 mb-1 mb-xl-0 d-flex justify-content-center">
          <popover-toggle v-if="index === 0" class="w-100" toggle-class="btn btn-sm btn-block btn-light text-muted">
            <template #toggle>
              <i class="help-icon fa-regular fa-circle-question"></i> {{ $t('Help') }}
            </template>
            <template #content>
              <!-- eslint-disable-next-line @stylistic/js/max-len -->
              {{ $t('This menu allows searching the generic extra metadata of records, including keys, types and different kinds of values based on the selected types. Multiple such queries can be combined with an "AND" or an "OR" operation in the form of "(Q1 AND Q2) OR (Q3 AND Q4)".') }}
              <hr class="my-1">
              <!-- eslint-disable-next-line @stylistic/js/max-len -->
              {{ $t('Note that keys inside of nested metadata entries are indexed in the form of "key_1.key_2". In case of list entries, keys are replaced by the corresponding index in the list instead, starting at 1.') }}
            </template>
          </popover-toggle>
          <select v-if="index > 0" v-model="query.link" class="custom-select custom-select-sm">
            <option v-for="link in links" :key="link[0]" :value="link[0]">{{ link[1] }}</option>
          </select>
        </div>
        <div class="col-xl-2 mb-1 mb-xl-0">
          <div class="input-group input-group-sm">
            <div class="input-group-prepend">
              <span class="input-group-text">{{ $t('Type') }}</span>
            </div>
            <select v-model="query.type" class="custom-select custom-select-sm">
              <option value=""></option>
              <option v-for="type in types" :key="type[0]" :value="type[0]">{{ type[1] }}</option>
            </select>
          </div>
        </div>
        <div class="mb-1 mb-xl-0" :class="{'col-xl-3': query.type, 'col-xl-8': !query.type}">
          <div class="input-group input-group-sm">
            <div class="input-group-prepend">
              <span class="input-group-text">{{ $t('Key') }}</span>
            </div>
            <input v-model="query.key" class="form-control" @keydown.enter="search">
            <div class="input-group-append">
              <button type="button"
                      class="btn btn-light"
                      :disabled="!query.key"
                      :title="$t('Toggle exact match')"
                      @click="toggleQuotation(query, 'key')">
                <i class="fa-solid fa-quote-left"></i>
              </button>
            </div>
          </div>
        </div>
        <div v-if="query.type === 'str'" class="col-xl-5 mb-1 mb-xl-0">
          <div class="input-group input-group-sm">
            <div class="input-group-prepend">
              <span class="input-group-text">{{ $t('Value') }}</span>
            </div>
            <input v-model="query.str" class="form-control" @keydown.enter="search">
            <div class="input-group-append">
              <button type="button"
                      class="btn btn-light"
                      :disabled="!query.str"
                      :title="$t('Toggle exact match')"
                      @click="toggleQuotation(query, 'str')">
                <i class="fa-solid fa-quote-left"></i>
              </button>
            </div>
          </div>
        </div>
        <div v-if="query.type === 'numeric'" class="col-xl-3 mb-1 mb-xl-0">
          <div class="d-flex justify-content-between">
            <div class="input-group input-group-sm mr-1">
              <div class="input-group-prepend">
                <span class="input-group-text">&ge;</span>
              </div>
              <input v-model="query.numeric.min" class="form-control" @keydown.enter="search">
            </div>
            <div class="input-group input-group-sm ml-1">
              <div class="input-group-prepend">
                <span class="input-group-text">&le;</span>
              </div>
              <input v-model="query.numeric.max" class="form-control" @keydown.enter="search">
            </div>
          </div>
        </div>
        <div v-if="query.type === 'numeric'" class="col-xl-2 mb-1 mb-xl-0">
          <div class="input-group input-group-sm">
            <div class="input-group-prepend">
              <span class="input-group-text">{{ $t('Unit') }}</span>
            </div>
            <input v-model="query.numeric.unit" class="form-control" @keydown.enter="search">
          </div>
        </div>
        <div v-if="query.type === 'bool'" class="col-xl-5 mb-1 mb-xl-0">
          <div class="input-group input-group-sm">
            <div class="input-group-prepend">
              <span class="input-group-text">{{ $t('Value') }}</span>
            </div>
            <select v-model="query.bool" class="custom-select">
              <option value=""></option>
              <option value="true">true</option>
              <option value="false">false</option>
            </select>
          </div>
        </div>
        <div v-if="query.type === 'date'" class="col-xl-5 mb-1 mb-xl-0">
          <div class="d-flex justify-content-between">
            <div class="input-group input-group-sm mr-1">
              <div class="input-group-prepend">
                <span class="input-group-text">&ge;</span>
              </div>
              <date-time-picker :initial-value="query.date.min" @input="query.date.min = $event"></date-time-picker>
            </div>
            <div class="input-group input-group-sm ml-1">
              <div class="input-group-prepend">
                <span class="input-group-text">&le;</span>
              </div>
              <date-time-picker :initial-value="query.date.max" @input="query.date.max = $event"></date-time-picker>
            </div>
          </div>
        </div>
        <div class="col-xl-1 btn-group btn-group-sm">
          <button type="button" class="btn btn-light" :title="$t('Add search field')" @click="addQuery(null, index)">
            <i class="fa-solid fa-plus"></i>
          </button>
          <button v-if="queries.length > 1"
                  type="button"
                  class="btn btn-light"
                  :title="$t('Remove search field')"
                  @click="removeQuery(index)">
            <i class="fa-solid fa-xmark"></i>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped lang="scss">
.help-icon {
  display: inline;

  @media (min-width: 1200px) and (max-width: 1400px) {
    display: none;
  }
}
</style>

<script>
export default {
  props: {
    queryString: String,
  },
  emits: ['change', 'search'],
  data() {
    return {
      queries: [],
      links: [['and', $t('AND')], ['or', $t('OR')]],
      types: [['str', 'String'], ['numeric', $t('Numeric')], ['bool', 'Boolean'], ['date', 'Date']],
    };
  },
  watch: {
    queries: {
      handler() {
        const results = [];

        for (const query of this.queries) {
          // A query needs at least a type or key in order to be included in the serialized result.
          if (!query.type && !query.key) {
            continue;
          }

          const result = {};

          for (const prop of ['link', 'type', 'key']) {
            if (query[prop]) {
              result[prop] = query[prop];
            }
          }

          if (query.type === 'numeric') {
            result.numeric = {};

            for (const prop of ['min', 'max', 'unit']) {
              if (query.numeric[prop]) {
                result.numeric[prop] = query.numeric[prop];
              }
            }

            if (Object.keys(result.numeric).length === 0) {
              delete result.numeric;
            }
          } else if (query.type === 'date') {
            result.date = {};

            for (const prop of ['min', 'max']) {
              if (query.date[prop]) {
                result.date[prop] = query.date[prop];
              }
            }

            if (Object.keys(result.date).length === 0) {
              delete result.date;
            }
          } else if (query.type && query[query.type]) {
            result[query.type] = query[query.type];
          }

          results.push(result);
        }

        this.$emit('change', JSON.stringify(results));
      },
      deep: true,
    },
  },
  mounted() {
    try {
      const queries = JSON.parse(this.queryString);

      if (kadi.utils.isArray(queries) && queries.length > 0) {
        queries.forEach((query) => this.addQuery(query));
      } else {
        this.addQuery();
      }
    } catch {
      this.addQuery();
    }
  },
  methods: {
    toggleQuotation(query, prop) {
      if (kadi.utils.isQuoted(query[prop])) {
        query[prop] = query[prop].slice(1, query[prop].length - 1);
      } else {
        query[prop] = `"${query[prop]}"`;
      }
    },
    addQuery(query = null, index = null) {
      const newQuery = {
        id: kadi.utils.randomAlnum(),
        link: 'and',
        type: null,
        key: null,
        str: null,
        numeric: {min: null, max: null, unit: null},
        bool: null,
        date: {min: null, max: null},
      };

      if (query) {
        for (const prop of ['link', 'type', 'key']) {
          newQuery[prop] = query[prop] || newQuery[prop];
        }

        // Validate at least the type, since it is used to set the corresponding values and to conditionally render the
        // corresponding inputs.
        if (!this.types.map((type) => type[0]).includes(newQuery.type)) {
          newQuery.type = null;
        }

        const type = newQuery.type;

        if (type === 'numeric') {
          if (query.numeric) {
            for (const prop of ['min', 'max', 'unit']) {
              newQuery.numeric[prop] = query.numeric[prop] || newQuery.numeric[prop];
            }
          }
        } else if (type === 'date') {
          if (query.date) {
            for (const prop of ['min', 'max']) {
              newQuery.date[prop] = query.date[prop] || newQuery.date[prop];
            }
          }
        } else if (type) {
          newQuery[type] = query[type] || newQuery[type];
        }
      }

      kadi.utils.addToArray(this.queries, newQuery, index);
    },
    removeQuery(index) {
      this.queries.splice(index, 1);
    },
    search() {
      this.$emit('search');
    },
  },
};
</script>
