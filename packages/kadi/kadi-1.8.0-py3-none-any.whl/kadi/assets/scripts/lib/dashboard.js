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

import {GridLayout} from 'scripts/lib/grid.js';

export default class Dashboard {
  constructor(name, layout = new GridLayout(window.crypto.randomUUID()), panels = {}, layoutAssignments = {}) {
    this.name = name;
    this.layout = layout;
    this.panels = panels;
    this.layoutAssignments = layoutAssignments;
  }

  static from(other) {
    if (!['name', 'layout', 'panels', 'layoutAssignments'].every((key) => key in other)) {
      return null;
    }

    return new Dashboard(
      other.name,
      GridLayout.from(other.layout),
      kadi.utils.deepClone(other.panels),
      kadi.utils.deepClone(other.layoutAssignments),
    );
  }

  createPanel(panelType) {
    return {
      id: window.crypto.randomUUID(),
      type: panelType,
      title: $t('Title'),
      subtitle: '',
      settings: {},
    };
  }

  removePanel(panel, columnId) {
    delete this.layoutAssignments[columnId];
    delete this.panels[panel.id];
  }

  getPanelByColumnId(columnId) {
    const panelId = columnId in this.layoutAssignments ? this.layoutAssignments[columnId] : null;
    return panelId in this.panels ? this.panels[panelId] : null;
  }

  toJSON() {
    return {
      name: this.name,
      layout: this.layout.toJSON(),
      panels: this.panels,
      layoutAssignments: this.layoutAssignments,
    };
  }
}
