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
    <div v-for="(itemGroup, groupIndex) in groupedItems"
         :key="itemGroup.id"
         class="card-deck"
         :class="{'mb-4': groupIndex < groupedItems.length - 1}">
      <div v-for="index in numCards"
           :key="index"
           class="card card-action mb-0"
           :class="{'border-0': index > itemGroup.items.length}">
        <slot v-if="index - 1 < itemGroup.items.length" :item="itemGroup.items[index - 1]"></slot>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  props: {
    items: Array,
    maxCards: {
      type: Number,
      default: 3,
    },
    isResponsive: {
      type: Boolean,
      default: true,
    },
  },
  data() {
    return {
      numCards: this.maxCards,
    };
  },
  computed: {
    groupedItems() {
      const items = [];

      for (let i = 0; i < this.items.length; i += this.numCards) {
        const itemGroup = {id: i, items: []};

        for (let j = i; j < this.items.length && j < i + this.numCards; j++) {
          itemGroup.items.push(this.items[j]);
        }
        items.push(itemGroup);
      }
      return items;
    },
  },
  mounted() {
    if (this.isResponsive) {
      this.adjustNumCards();
      window.addEventListener('resize', this.adjustNumCards);
    }
  },
  unmounted() {
    window.removeEventListener('resize', this.adjustNumCards);
  },
  methods: {
    adjustNumCards() {
      // Corresponds to the MD Bootstrap breakpoint.
      if (window.innerWidth < 768) {
        this.numCards = Math.round(this.maxCards / 3);
      // Corresponds to the XL Bootstrap breakpoint.
      } else if (window.innerWidth < 1200) {
        this.numCards = Math.round(this.maxCards / 2);
      } else {
        this.numCards = this.maxCards;
      }
    },
  },
};
</script>
