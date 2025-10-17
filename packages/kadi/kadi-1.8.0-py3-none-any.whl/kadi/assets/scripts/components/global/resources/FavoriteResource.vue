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
  <button type="button"
          class="btn btn-sm btn-light my-1"
          :title="title"
          :disabled="disableFavorite"
          @click="toggleFavorite">
    <i v-if="isFavorite_" class="fa-solid fa-star"></i>
    <i v-else class="fa-regular fa-star"></i>
  </button>
</template>

<script>
export default {
  props: {
    isFavorite: Boolean,
    favoriteEndpoint: String,
  },
  data() {
    return {
      isFavorite_: this.isFavorite,
      disableFavorite: false,
    };
  },
  computed: {
    title() {
      return this.isFavorite_ ? $t('Unfavorite') : $t('Favorite');
    },
  },
  methods: {
    async toggleFavorite() {
      this.disableFavorite = true;

      try {
        await axios.patch(this.favoriteEndpoint);
        this.isFavorite_ = !this.isFavorite_;
      } catch (error) {
        kadi.base.flashDanger($t('Error favoriting resource.'), error.request);
      } finally {
        this.disableFavorite = false;
      }
    },
  },
};
</script>
