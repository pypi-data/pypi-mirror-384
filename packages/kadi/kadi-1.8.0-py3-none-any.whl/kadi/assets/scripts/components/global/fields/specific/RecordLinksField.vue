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
    <div class="form-group">
      <div class="row align-items-end">
        <div class="col-sm-6">
          <label class="form-control-label">{{ field.label }}</label>
        </div>
        <div class="col-sm-6 d-sm-flex justify-content-end mb-2">
          <button type="button"
                  class="btn btn-sm btn-light"
                  :class="{'toggle-active': showPreview}"
                  @click="showPreview = !showPreview">
            <i class="fa-solid fa-eye"></i> {{ $t('Link preview') }}
          </button>
        </div>
      </div>
      <div class="card">
        <div class="card-body p-2">
          <div v-for="(link, index) in links" :key="link.id">
            <div v-if="showPreview && (link.record !== null || link.name !== null)" class="card bg-light mb-1">
              <div class="card-body py-1 px-2">
                <div class="row align-items-center">
                  <div class="col-md-4">
                    <small>
                      <span v-if="currentRecordIdentifier" :title="currentRecordIdentifier">
                        @{{ kadi.utils.truncate(currentRecordIdentifier, 25) }}
                      </span>
                      <em v-else>{{ $t('This record') }}</em>
                    </small>
                  </div>
                  <div class="col-md-4 d-md-flex justify-content-center">
                    <span>
                      <i v-if="link.direction === 'in'" class="fa-solid fa-arrow-left-long fa-lg mr-2"></i>
                      <small>{{ kadi.utils.truncate(link.name || '', 20) }}</small>
                      <i v-if="link.direction === 'out'" class="fa-solid fa-arrow-right-long fa-lg ml-2"></i>
                    </span>
                  </div>
                  <div class="col-md-4 d-md-flex justify-content-end">
                    <small>
                      <span v-if="link.record" :title="link.record[1]">
                        {{ kadi.utils.truncate(link.record[1], 25) }}
                      </span>
                      <em v-else>{{ $t('Linked record') }}</em>
                    </small>
                  </div>
                </div>
              </div>
            </div>
            <div class="form-row" :class="{'mb-3' : index < links.length - 1 && !link.editTerm}">
              <div class="col-md-3 mb-1 mb-md-0">
                <div class="input-group input-group-sm">
                  <div class="input-group-prepend">
                    <span class="input-group-text">{{ $t('Direction') }}</span>
                  </div>
                  <select v-model="link.direction" class="custom-select">
                    <option v-for="direction in directions" :key="direction[0]" :value="direction[0]">
                      {{ direction[1] }}
                    </option>
                  </select>
                </div>
              </div>
              <div class="col-md-4 mb-1 mb-md-0">
                <div class="input-group input-group-sm">
                  <div class="input-group-prepend">
                    <span class="input-group-text">{{ $t('Record') }}</span>
                  </div>
                  <dynamic-selection container-classes="select2-single-sm"
                                     :class="{'has-error': getErrors(index, 'record').length > 0}"
                                     :endpoint="recordsEndpoint"
                                     :initial-values="getInitialRecord(link)"
                                     :placeholder="$t('Search for records')"
                                     @select="selectRecord(link, $event)"
                                     @unselect="link.record = null">
                  </dynamic-selection>
                </div>
                <div v-for="error in getErrors(index, 'record')" :key="error" class="invalid-feedback">{{ error }}</div>
              </div>
              <div class="col-md-3 mb-1 mb-md-0">
                <div class="input-group input-group-sm">
                  <div class="input-group-prepend">
                    <span class="input-group-text">{{ $t('Name') }}</span>
                  </div>
                  <dynamic-selection container-classes="select2-single-sm"
                                     :class="{'has-error': getErrors(index, 'name').length > 0}"
                                     :endpoint="namesEndpoint"
                                     :initial-values="getInitialName(link)"
                                     :placeholder="$t('Enter or search for a name')"
                                     :max-input-length="field.validation.max.name"
                                     :tags="true"
                                     @select="selectName(link, $event)"
                                     @unselect="link.name = null">
                  </dynamic-selection>
                  <div class="input-group-append">
                    <button type="button"
                            class="input-group-text btn btn-light"
                            :class="{'toggle-active': link.editTerm}"
                            :title="$t('Toggle term IRI')"
                            @click="link.editTerm = !link.editTerm">
                      <i class="fa-solid fa-link"></i>
                    </button>
                  </div>
                </div>
                <div v-for="error in getErrors(index, 'name')" :key="error" class="invalid-feedback">{{ error }}</div>
              </div>
              <div class="col-md-2">
                <div class="btn-group btn-group-sm w-100">
                  <button type="button" class="btn btn-light" :title="$t('Add link')" @click="addLink(null, index)">
                    <i class="fa-solid fa-plus"></i>
                  </button>
                  <button v-if="links.length > 1"
                          type="button"
                          class="btn btn-light"
                          :title="$t('Remove link')"
                          @click="removeLink(index)">
                    <i class="fa-solid fa-xmark"></i>
                  </button>
                </div>
              </div>
            </div>
            <div v-show="link.editTerm" class="mt-1" :class="{'mb-3' : index < links.length - 1}">
              <div class="input-group input-group-sm">
                <div class="input-group-prepend">
                  <span class="input-group-text">{{ $t('Term IRI') }}</span>
                </div>
                <input v-model.trim="link.term"
                       class="form-control"
                       :class="{'has-error': getErrors(index, 'term').length > 0}">
                <div v-if="termsEndpoint" class="input-group-append">
                  <button type="button" class="btn btn-light" @click="showTermSearch(link)">
                    <i class="fa-solid fa-search"></i> {{ $t('Find term') }}
                  </button>
                </div>
              </div>
              <div v-for="error in getErrors(index, 'term')" :key="error" class="invalid-feedback">{{ error }}</div>
              <small v-if="getErrors(index, 'term').length === 0" class="form-text text-muted">
                {{ $t('An IRI specifying an existing term that the link should represent.') }}
              </small>
            </div>
          </div>
        </div>
      </div>
      <small class="form-text text-muted">{{ field.description }}</small>
      <input type="hidden" :name="field.name" :value="serializedLinks">
    </div>
    <term-search v-if="termsEndpoint" ref="termSearch" :endpoint="termsEndpoint" @select-term="selectTerm">
    </term-search>
  </div>
</template>

<script>
export default {
  props: {
    field: Object,
    recordsEndpoint: String,
    namesEndpoint: String,
    termsEndpoint: {
      type: String,
      default: null,
    },
    currentRecordIdentifier: {
      type: String,
      default: null,
    },
  },
  data() {
    return {
      directions: [['out', $t('Outgoing')], ['in', $t('Incoming')]],
      links: [],
      showPreview: false,
      currentLink: null,
    };
  },
  computed: {
    serializedLinks() {
      const links = [];

      for (const link of this.links) {
        if (link.record !== null || link.name !== null) {
          links.push({
            record: link.record !== null ? link.record[0] : null,
            name: link.name,
            term: link.term || null,
            direction: link.direction,
          });
        }
      }

      return JSON.stringify(links);
    },
  },
  mounted() {
    for (const link of this.field.data) {
      this.addLink(link);
    }

    if (this.links.length === 0) {
      this.addLink();
    } else {
      for (const [index, link] of this.links.entries()) {
        if (this.getErrors(index, 'term').length > 0) {
          link.editTerm = true;
        }
      }
    }
  },
  methods: {
    getInitialRecord(link) {
      return link.record === null ? [] : [link.record];
    },
    getInitialName(link) {
      return link.name === null ? [] : [[link.name, link.name]];
    },
    getErrors(index, name) {
      const errors = this.field.errors[index];

      if (errors) {
        return errors[name] || [];
      }

      return [];
    },
    selectRecord(link, record) {
      link.record = [record.id, record.text];
      this.selectValue();
    },
    selectName(link, name) {
      link.name = name.id;
      this.selectValue();
    },
    selectValue() {
      // Automatically add a new link input if the last one is not empty.
      const lastLink = this.links[this.links.length - 1];

      if (lastLink.record !== null && lastLink.name !== null) {
        this.addLink();
      }

      // Dispatch a regular 'change' event from the element as well.
      this.$el.dispatchEvent(new Event('change', {bubbles: true}));
    },
    addLink(link = null, index = null) {
      const newLink = {
        id: kadi.utils.randomAlnum(),
        record: null,
        name: null,
        term: '',
        direction: this.directions[0][0],
        editTerm: false,
      };

      if (link !== null) {
        // Copy a given link.
        Object.assign(newLink, link);
      } else {
        // Try to copy the direction of the previous link.
        const prevIndex = index === null ? this.links.length - 1 : index;
        const prevLink = this.links[prevIndex];

        if (prevLink) {
          newLink.direction = prevLink.direction;
        }
      }

      kadi.utils.addToArray(this.links, newLink, index);
    },
    removeLink(index) {
      this.links.splice(index, 1);
    },
    showTermSearch(link) {
      this.currentLink = link;
      this.$refs.termSearch.open(link.name || '');
    },
    selectTerm(term) {
      this.currentLink.term = term;
      // Dispatch a regular 'change' event from the element as well.
      this.$el.dispatchEvent(new Event('change', {bubbles: true}));
    },
  },
};
</script>
