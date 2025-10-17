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

import {createApp} from 'vue';

// Load all components inside 'srcipts/components/global'.
const requireComponent = import.meta.webpackContext('../components/global', {recursive: true, regExp: /\.vue$/});
const globalComponents = {};

requireComponent.keys().forEach((fileName) => {
  globalComponents[fileName.split('/').pop().replace(/\.\w+$/, '')] = requireComponent(fileName).default;
});

function trimEmptyTextNodes(el) {
  for (const node of el.childNodes) {
    if (node.nodeType === window.Node.TEXT_NODE && node.data.trim() === '') {
      node.remove();
    }
  }
}

export function newVue(options = {}, exposeApp = true) {
  const app = createApp(options);

  // For using Vue and Jinja in the same template. Only relevant outside of SFCs.
  app.config.compilerOptions.delimiters = ['{$', '$}'];
  app.config.compilerOptions.whitespace = 'preserve';

  app.config.globalProperties.kadi = kadi;
  app.config.globalProperties.$t = $t;

  app.directive('trim-ws', {
    mounted: trimEmptyTextNodes,
    updated: trimEmptyTextNodes,
  });

  for (const [name, component] of Object.entries(globalComponents)) {
    app.component(name, component);
  };

  if (exposeApp && window.kadi) {
    window.kadi.app = app;
  }

  return app;
}
