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
    <div class="input-group input-group-sm mb-2">
      <input :id="filterId" v-model.trim="filter" class="form-control" :placeholder="$t('Filter rows')">
      <clear-button :input-id="filterId" :input="filter" @clear-input="filter = ''"></clear-button>
    </div>
    <small v-if="encoding" class="text-muted">{{ $t('Detected encoding') }}: {{ encoding.toUpperCase() }}</small>
    <div class="table-responsive max-vh-75 mt-2">
      <table class="table table-sm table-bordered table-hover">
        <thead v-if="hasHeader" class="bg-light">
          <tr>
            <th v-for="(value, index) in headerRow" :key="index">
              <div class="cursor-pointer d-flex justify-content-between" @click="sortRow(index)">
                <strong>
                  <pre class="d-inline">{{ value }}</pre>
                </strong>
                <span v-if="sort.index === index" class="ml-2">
                  <i v-if="sort.direction === 'desc'" class="fa-solid fa-angle-up"></i>
                  <i v-if="sort.direction === 'asc'" class="fa-solid fa-angle-down"></i>
                </span>
              </div>
            </th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(row, rowIndex) in displayedDataRows" :key="rowIndex">
            <td v-for="(value, valueIndex) in row" :key="valueIndex">
              <pre class="mb-0">{{ value }}</pre>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script>
export default {
  props: {
    rows: Array,
    encoding: {
      type: String,
      default: null,
    },
    hasHeader: {
      type: Boolean,
      default: false,
    },
  },
  data() {
    return {
      filter: '',
      sort: {
        index: null,
        direction: null,
      },
      headerRow: [],
      dataRows: [],
      displayedDataRows: [],
      filterId: kadi.utils.randomAlnum(),
    };
  },
  watch: {
    rows: {
      handler() {
        this.initRows();
      },
      deep: 1,
    },
    filter() {
      this.updateDisplayedRows();
    },
  },
  mounted() {
    this.initRows();
  },
  methods: {
    initRows() {
      if (this.hasHeader) {
        this.headerRow = this.rows[0];
        this.dataRows = this.displayedDataRows = this.rows.slice(1, this.rows.length);
      } else {
        this.dataRows = this.displayedDataRows = this.rows;
      }
    },
    filterRows(rows, filter) {
      const filterLower = filter.toLowerCase();
      const filteredRows = [];

      for (const row of rows) {
        for (const value of row) {
          if (value.toLowerCase().includes(filterLower)) {
            filteredRows.push(row);
            break;
          }
        }
      }

      return filteredRows;
    },
    sortRows(rows, index, direction) {
      if (!direction) {
        return rows;
      }

      return rows.sort((a, b) => {
        if (direction === 'desc') {
          return a[index] > b[index];
        }
        return a[index] < b[index];
      });
    },
    updateDisplayedRows() {
      const filteredRows = this.filterRows(this.dataRows, this.filter);
      this.displayedDataRows = this.sortRows(filteredRows, this.sort.index, this.sort.direction);
    },
    sortRow(index) {
      if (this.sort.index !== index) {
        this.sort.direction = null;
      }
      this.sort.index = index;

      if (!this.sort.direction) {
        this.sort.direction = 'desc';
      } else if (this.sort.direction === 'desc') {
        this.sort.direction = 'asc';
      } else {
        this.sort.direction = null;
      }

      this.updateDisplayedRows();
    },
  },
};
</script>
