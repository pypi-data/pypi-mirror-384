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

<script setup>
import {onMounted, ref, watch} from 'vue';

import markdownit from 'markdown-it';
import pluginSub from 'markdown-it-sub';
import pluginSup from 'markdown-it-sup';
import pluginTexmath from 'markdown-it-texmath';

const props = defineProps({
  input: String,
});

const result = ref('');

let md = null;

function render() {
  result.value = md.render(props.input);
}

watch(() => props.input, render);

onMounted(() => {
  md = markdownit()
    .use(pluginSub)
    .use(pluginSup)
    .use(pluginTexmath, {outerSpace: true, katexOptions: {output: 'html', maxSize: 10, maxExpand: 100}});

  // Customize some of the rendering rules.
  md.renderer.rules.heading_open = (tokens, idx, options, env, self) => {
    const token = tokens[idx];
    const sizes = [1.8, 1.6, 1.4, 1.2, 1.1, 1.0];
    const level = token.markup.length - 1;

    token.attrSet('class', 'font-weight-bold');
    token.attrSet('style', `font-size: ${sizes[level]}rem`);

    return self.renderToken(tokens, idx, options);
  };

  md.renderer.rules.link_open = (tokens, idx, options, env, self) => {
    const token = tokens[idx];

    token.attrSet('target', '_blank');
    token.attrSet('rel', 'noopener noreferrer');
    token.attrSet('style', 'color: inherit; text-decoration: underline');

    return self.renderToken(tokens, idx, options);
  };

  md.renderer.rules.table_open = (tokens, idx, options, env, self) => {
    const token = tokens[idx];

    token.attrSet('class', 'table table-sm table-bordered table-hover');
    token.attrSet('style', 'color: inherit');

    return self.renderToken(tokens, idx, options);
  };

  const imageRenderer = md.renderer.rules.image;

  md.renderer.rules.image = (tokens, idx, options, env, self) => {
    const token = tokens[idx];
    const src = token.attrGet('src') || '';

    // For images (presumably) loaded via Kadi, we only use the path of the image source to stay domain-independent,
    // which also ensures that even full URLs with an incorrect or old domain work correctly.
    if (src.includes('/api/records')) {
      let srcPath = '';

      // The URL might already be specified without a domain.
      try {
        srcPath = new URL(src).pathname;
      } catch {
        srcPath = src;
      }

      token.attrSet('src', srcPath);
    }

    // Allow resizing of images via their alt attribute (which seems to have some special handling and can't be
    // retrieved like a regular attribute at this point).
    const child = token.children.length > 0 ? token.children[0] : null;

    if (child && child.content) {
      const match = child.content.match(/^(.*)\|(\d*)(?:x(\d*))?$/);

      if (match) {
        const [, content, width, height] = match;

        child.content = content;
        token.attrSet('width', width);
        token.attrSet('height', height);
      }
    }

    let maxWidth = '33%';

    if (token.attrGet('width') || token.attrGet('height')) {
      maxWidth = '100%';
    }

    token.attrSet('style', `max-width: ${maxWidth}`);
    token.attrSet('loading', 'lazy');

    const result = imageRenderer(tokens, idx, options, env, self);
    return `<a href="${src}" target="_blank" rel="noopener noreferrer">${result}</a>`;
  };

  render();
});
</script>

<template>
  <span class="markdown" v-html="result"></span>
</template>

<style scoped>
.markdown :last-child {
  margin-bottom: 0;
}
</style>
