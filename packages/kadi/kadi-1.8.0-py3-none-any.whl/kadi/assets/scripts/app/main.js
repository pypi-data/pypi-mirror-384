/* Copyright 2020 Karlsruhe Institute of Technology
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

import 'styles/main.scss';

import {continueTour, hasProgress, initializeTour, startTour, tourActive} from 'scripts/lib/tour/core.js';
import {newVue} from 'scripts/lib/core.js';
import utils from 'scripts/lib/utils.js';

import BroadcastMessage from 'scripts/components/lib/base/BroadcastMessage.vue';
import FlashMessage from 'scripts/components/lib/base/FlashMessage.vue';
import FlashMessages from 'scripts/components/lib/base/FlashMessages.vue';
import HelpItem from 'scripts/components/lib/base/HelpItem.vue';
import LocaleChooser from 'scripts/components/lib/base/LocaleChooser.vue';
import NotificationManager from 'scripts/components/lib/base/NotificationManager.vue';
import QuickSearch from 'scripts/components/lib/base/QuickSearch.vue';
import RecentlyVisited from 'scripts/components/lib/base/RecentlyVisited.vue';

// Namespace for global utility functions.
kadi.utils = utils;

// Namespace for global base functionality and utility functions of base Vue apps.
kadi.base = {
  // For instantiating the base Vue app within inline scripts.
  newVue,
};

// Scroll required inputs to a more sensible location, also taking different page layouts into account.
document.addEventListener('invalid', (e) => kadi.utils.scrollIntoView(e.target), true);

// Vue app for the locale chooser in the navigation footer.
newVue(
  {components: {LocaleChooser}},
  false,
).mount('#base-locale-chooser');

// Vue app for handling flash messages.
const flashMessages = newVue(
  {components: {FlashMessages, FlashMessage}},
  false,
).mount('#base-flash-messages').$refs.component;

Object.assign(kadi.base, {
  flashDanger: flashMessages.flashDanger,
  flashInfo: flashMessages.flashInfo,
  flashSuccess: flashMessages.flashSuccess,
  flashWarning: flashMessages.flashWarning,
});

// Vue app for handling recently visited resources. Instantiated here so non-active users' items can be cleared.
const recentlyVisited = newVue(
  {components: {RecentlyVisited}},
  false,
).mount('#base-recently-visited').$refs.component;

kadi.base.visitItem = recentlyVisited.addItem;

if (kadi.globals.showBroadcast) {
  // Vue app for the global broadcast message, if applicable.
  newVue(
    {components: {BroadcastMessage}},
    false,
  ).mount('#base-broadcast-message');
}

// Initializations that should only be performed for active users.
if (kadi.globals.userActive) {
  // Register global keyboard shortcuts.
  const keyMap = {
    'H': '',
    'R': 'records',
    'C': 'collections',
    'T': 'templates',
    'U': 'users',
    'G': 'groups',
  };

  // Do nothing if the user is either within an input field or if a tour is currently active.
  document.addEventListener('keydown', (e) => {
    if (['INPUT', 'SELECT', 'TEXTAREA'].includes(e.target.tagName)
        || e.target.contentEditable === 'true'
        || tourActive()) {
      return;
    }

    if (e.shiftKey && !e.ctrlKey && !e.altKey && !e.metaKey) {
      for (const [key, endpoint] of Object.entries(keyMap)) {
        if (e.key === key) {
          e.preventDefault();
          window.location.href = `/${endpoint}`;
          return;
        }
      }
    }
  });

  // Namespace for global tour functionality.
  kadi.base.tour = {
    continue: continueTour,
    hasProgress,
    initialize: initializeTour,
    start: startTour,
  };

  // Vue app for the quick search in the navigation bar.
  newVue(
    {components: {QuickSearch}},
    false,
  ).mount('#base-quick-search');

  // Vue app for the help item in the navigation bar.
  newVue(
    {components: {HelpItem}},
    false,
  ).mount('#base-help-item');

  // Vue app for handling notifications.
  const notificationManager = newVue(
    {components: {NotificationManager}},
    false,
  ).mount('#base-notification-manager').$refs.component;

  kadi.base.getNotifications = notificationManager.getNotifications;
}

// Initializations that should only be performed in production environments.
if (kadi.globals.environment === 'production') {
  console.info('If you found a bug, please report it at https://gitlab.com/iam-cms/kadi');
}

// Stop the logo animation once the current animation iteration is finished.
document.querySelectorAll('.kadi-logo').forEach((el) => {
  el.addEventListener('animationiteration', () => el.style.animation = 'none');
  el.addEventListener('webkitAnimationIteration', () => el.style.animation = 'none');
});
