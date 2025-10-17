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

import {autoPlacement, offset} from '@floating-ui/dom';
import Shepherd from 'shepherd.js';

import basicTour from 'basic';

const tourGroups = {
  basic: basicTour,
};

const storageKey = 'tour_progress';
const queryParam = 'tour';

function getNavbarElem() {
  return document.getElementById('base-navbar');
}

function clearProgress() {
  window.localStorage.removeItem(storageKey);
}

function setProgress(groupID, tourID, stepID, persist = true) {
  const progress = {
    group: groupID,
    tour: tourID,
    step: stepID,
    url: window.location.pathname,
  };

  if (persist) {
    window.localStorage.setItem(storageKey, JSON.stringify(progress));
  }

  // Globally dispatch a custom event as well in order to react to the progress of a tour.
  window.dispatchEvent(new CustomEvent('kadi-tour-progress', {detail: progress}));
}

function getProgress() {
  try {
    const progress = JSON.parse(window.localStorage.getItem(storageKey));
    const url = progress.url;

    const tourGroup = tourGroups[progress.group];

    const tourMetaIndex = tourGroup.findIndex((t) => t.id === progress.tour);
    const tourMeta = tourGroup[tourMetaIndex];

    const stepMetaIndex = tourMeta.steps.findIndex((s) => s.id === progress.step);
    const stepMeta = tourMeta.steps[stepMetaIndex];

    if (!url || !stepMeta) {
      clearProgress();
      return null;
    }

    return {
      url,
      group: {
        id: progress.group,
        tours: tourGroup,
      },
      tour: {
        index: tourMetaIndex,
        meta: tourMeta,
      },
      step: {
        index: stepMetaIndex,
        meta: stepMeta,
      },
    };
  } catch {
    clearProgress();
    return null;
  }
}

export function hasProgress(groupID = null) {
  const progress = getProgress();
  return progress !== null && (groupID === null || progress.group.id === groupID);
}

export function tourActive() {
  return Boolean(Shepherd.activeTour);
}

export function startTour(groupID, tourID = null, stepID = null) {
  const tourGroup = tourGroups[groupID];
  let tourMetaIndex = 0;

  if (tourID !== null) {
    tourMetaIndex = tourGroup.findIndex((t) => t.id === tourID);
  }

  const tourMeta = tourGroup[tourMetaIndex];

  const tour = new Shepherd.Tour({
    defaultStepOptions: {
      arrow: false,
      cancelIcon: {enabled: true},
      floatingUIOptions: {middleware: [autoPlacement(), offset({mainAxis: 15})]},
      modalOverlayOpeningPadding: 5,
      modalOverlayOpeningRadius: 5,
      scrollTo: true,
      scrollToHandler: (element) => {
        if (element) {
          kadi.utils.scrollIntoView(element);
        }
      },
      title: tourMeta.header,
    },
    keyboardNavigation: false,
    tourName: tourMeta.id,
    useModalOverlay: true,
  });

  for (const [index, step] of tourMeta.steps.entries()) {
    const buttons = [];

    // Back button to switch to the previous step.
    if (index > 0) {
      buttons.push({
        text: `<i class="fa-solid fa-arrow-left mr-2"></i> ${$t('Back')}`,
        action() {
          this.back();
        },
      });
    }

    // Next button to switch to the next step.
    if (index < tourMeta.steps.length - 1) {
      buttons.push({
        text: `${$t('Next')} <i class="fa-solid fa-arrow-right ml-2"></i>`,
        action() {
          this.next();
        },
      });
    }

    // Close button to complete the tour on the last tour and step.
    if (tourMetaIndex >= tourGroup.length - 1 && index >= tourMeta.steps.length - 1) {
      buttons.push({
        text: $t('Close'),
        action() {
          this.complete();
        },
      });
    }

    let elem = null;

    // If no element was given, use the step ID as part of a corresponding custom tour meta attribute.
    if (step.attach) {
      elem = step.elem || `[data-tour="${step.id}"]`;
    }

    tour.addStep({
      attachTo: {
        element: elem,
        on: 'bottom',
      },
      buttons,
      canClickTarget: step.clickable || false,
      id: step.id,
      text: step.content,
      when: {
        show() {
          setProgress(groupID, tourMeta.id, this.options.id);

          // Deactivate the navbar manually if it is not highlighted itself, since it may still allow pointer events
          // otherwise due to its possibly fixed position.
          const navbarElem = getNavbarElem();
          navbarElem.style.pointerEvents = '';

          if (elem !== null && !navbarElem.contains(document.querySelector(elem))) {
            navbarElem.style.pointerEvents = 'none';
          }

          // Add a horizontal line before the footer.
          const footer = this.el.getElementsByClassName('shepherd-footer')[0];
          const hr = document.createElement('hr');
          hr.classList.add('my-0');
          footer.before(hr);

          // Adjust the layout of the close button.
          const closeButton = this.el.getElementsByClassName('shepherd-cancel-icon')[0];
          const closeIcon = document.createElement('i');
          closeIcon.classList.add('fa-solid', 'fa-xmark', 'fa-xs');
          closeButton.childNodes[0].replaceWith(closeIcon);

          // Add an indicator if the step allows clicking the target.
          if (this.options.canClickTarget) {
            const clickIcon = document.createElement('i');
            clickIcon.classList.add(
              'fa-solid',
              'fa-hand-pointer',
              'fa-xl',
              'text-primary',
              'align-self-center',
              'flex-grow-1',
            );
            footer.insertBefore(clickIcon, footer.firstChild);
          }
        },
      },
    });
  }

  const clickHandler = (e) => {
    // Cancel the tour when trying to submit a form.
    if (e.target.tagName === 'INPUT' && e.target.type === 'submit') {
      tour.cancel();
    }
  };

  document.addEventListener('click', clickHandler);

  // Perform some cleanup when completing or canceling the tour.
  ['complete', 'cancel'].forEach((event) => {
    tour.on(event, () => {
      document.removeEventListener('click', clickHandler);

      // Activate the navbar again, if applicable.
      getNavbarElem().style.pointerEvents = '';

      // Clear the progress if we are on the last tour and step.
      const progress = getProgress();
      if (progress
          && progress.group.id === groupID
          && progress.tour.index >= progress.group.tours.length - 1
          && progress.step.index >= progress.tour.meta.steps.length - 1) {
        clearProgress();
      }
    });
  });

  // Actually start the tour with the correct step, if applicable.
  tour.start();

  if (stepID !== null) {
    tour.show(stepID);
  }

  // In order to trigger the progress event.
  setProgress(groupID, tourMeta.id, stepID || tourMeta.steps[0].id, false);
}

export function continueTour() {
  const progress = getProgress();

  if (!progress) {
    return;
  }

  if (progress.url === window.location.pathname) {
    // We are on the correct page already and can simply continue the tour.
    startTour(progress.group.id, progress.tour.meta.id, progress.step.meta.id);
  } else {
    // We need to switch the page using the query parameter to indicate that the tour should be continued.
    window.location.href = `${progress.url}?${queryParam}`;
  }
}

export function initializeTour(groupID, tourID) {
  const progress = getProgress();

  if (!progress || progress.group.id !== groupID) {
    return;
  }

  // If the query parameter is supplied we check if the progress matches what we expect before continuing the tour.
  if (kadi.utils.hasSearchParam(queryParam) && progress.tour.meta.id === tourID) {
    const url = kadi.utils.removeSearchParam(queryParam);
    kadi.utils.replaceState(url);

    startTour(groupID, tourID, progress.step.meta.id);
    return;
  }

  // Otherwise, check if the previous tour was just finished and if the next tour matches what we expect before
  // continuing the tour.
  const nextTourMeta = tourGroups[groupID][progress.tour.index + 1];

  if (nextTourMeta && nextTourMeta.id === tourID && progress.step.index >= progress.tour.meta.steps.length - 1) {
    startTour(groupID, tourID);
  }
}
