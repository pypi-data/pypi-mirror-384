<!-- Copyright 2022 Karlsruhe Institute of Technology
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
      <button type="button" class="btn btn-sm btn-light mb-2" @click="loadWorkbook">
        <i class="fa-solid fa-eye"></i> {{ $t('Load preview') }}
      </button>
    </div>
    <div v-else class="card">
      <div class="card-body p-1">
        <div v-if="!loading">
          <div v-if="currentSheet.length > 0" class="table-responsive max-vh-75 mb-3">
            <table class="sheet-table table table-sm table-bordered table-hover mb-0">
              <thead class="bg-light text-center">
                <tr>
                  <th></th>
                  <th v-for="(value, key) in currentSheet[0]" :key="key">{{ key }}</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(row, rowIndex) in currentSheet" :key="rowIndex">
                  <th class="bg-light align-middle text-center">{{ rowIndex + 1 }}</th>
                  <td v-for="(value, valueIndex) in row" :key="valueIndex">{{ value }}</td>
                </tr>
              </tbody>
            </table>
          </div>
          <em v-if="currentSheet.length === 0" class="text-muted ml-1">{{ $t('No content.') }}</em>
        </div>
        <div class="overflow-auto ws-nowrap">
          <span v-for="name in sheetNames"
                :key="name"
                class="sheet-nav btn btn-sm btn-light"
                :class="{'active': name === currentSheetName}"
                @click="loadSheet(name)">
            {{ name }}
          </span>
        </div>
        <div v-if="loading" class="text-muted ml-1">
          <i class="fa-solid fa-circle-notch fa-spin mr-1"></i> {{ $t('Loading workbook...') }}
        </div>
      </div>
    </div>
  </div>
</template>

<style lang="scss" scoped>
.sheet-nav {
  border-color: #dee2e6;
  border-radius: 0;

  &:not(:first-child) {
    margin-left: -1px;
  }

  &.active {
    background-color: #dbdbdb;
  }
}

.sheet-table {
  font-size: 0.825rem;
}
</style>

<script>
import xlsx from 'xlsx';

export default {
  props: {
    sheetUrl: String,
    fileSize: Number,
    maxFileSize: Number,
  },
  data() {
    return {
      workbook: null,
      sheetNames: [],
      sheets: {},
      currentSheetName: null,
      currentSheet: [],
      loading: true,
      forceLoad: false,
    };
  },
  mounted() {
    if (this.fileSize <= this.maxFileSize) {
      this.loadWorkbook();
    }
  },
  methods: {
    async loadWorkbook() {
      this.forceLoad = true;

      try {
        const response = await axios.get(this.sheetUrl, {responseType: 'arraybuffer'});

        try {
          this.workbook = xlsx.read(response.data, {
            cellDates: true,
            cellFormula: false,
            cellHTML: false,
            cellText: false,
          });
          this.sheetNames = this.workbook.SheetNames;
          this.loadSheet(this.sheetNames[0]);
        } catch (error) {
          console.error(error);
          kadi.base.flashDanger($t('Error parsing workbook.'));
        }
      } catch (error) {
        kadi.base.flashDanger($t('Error loading workbook.'), error.request);
      } finally {
        this.loading = false;
      }
    },
    loadSheet(name) {
      if (!this.sheets[name]) {
        this.sheets[name] = xlsx.utils.sheet_to_json(this.workbook.Sheets[name], {
          blankrows: true,
          dateNF: 'dd mmm yyyy hh:mm:ss',
          defval: '',
          header: 'A',
          raw: false,
        });
      }
      this.currentSheet = this.sheets[name];
      this.currentSheetName = name;
    },
  },
};
</script>;
