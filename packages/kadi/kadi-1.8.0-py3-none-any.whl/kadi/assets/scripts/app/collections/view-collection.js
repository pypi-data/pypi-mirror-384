/* Copyright 2023 Karlsruhe Institute of Technology
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

import CollectionLinksGraph from 'scripts/components/lib/graphs/CollectionLinksGraph.vue';

newVue({
  components: {
    CollectionLinksGraph,
  },
  data() {
    return {
      currentTab: null,
      includeChildCollections: false,
      renderLinksGraph: false,
      visualizeLinks: false,
      visualizeLinksParam: 'visualize',
    };
  },
  computed: {
    getRecordsEndpoint() {
      const baseEndpoint = kadi.context.get_records_endpoint;
      return this.includeChildCollections ? `${baseEndpoint}?children=true` : baseEndpoint;
    },
    searchRecordsEndpoint() {
      const baseEndpoint = kadi.context.search_records_endpoint;
      return this.includeChildCollections ? `${baseEndpoint}&child_collections=true` : baseEndpoint;
    },
  },
  watch: {
    visualizeLinks() {
      if (this.visualizeLinks) {
        // If we render the links graph component before it is shown, its size cannot be initialized correctly.
        this.renderLinksGraph = true;
      }

      const url = kadi.utils.setSearchParam(this.visualizeLinksParam, this.visualizeLinks);
      kadi.utils.replaceState(url);
    },
  },
  created() {
    const visualizeLinks = kadi.utils.getSearchParam(this.visualizeLinksParam);

    if (visualizeLinks === 'true') {
      this.visualizeLinks = true;
    }
  },
  mounted() {
    const collection = kadi.context.collection;
    kadi.base.visitItem('collection', collection.title, collection.identifier, `/collections/${collection.id}`);
  },
  methods: {
    changeTab(tab) {
      this.currentTab = tab;

      let url = null;

      if (this.currentTab === 'links') {
        url = kadi.utils.setSearchParam(this.visualizeLinksParam, this.visualizeLinks);
      } else {
        url = kadi.utils.removeSearchParam(this.visualizeLinksParam);
      }

      kadi.utils.replaceState(url);
    },
  },
});
