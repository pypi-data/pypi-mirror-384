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

/* eslint-disable @stylistic/js/max-len */

const tour = [
  {
    id: 'introduction',
    header: $t('Introduction'),
    steps: [
      {
        id: 'introduction',
        content: $t('This interactive tour will introduce you to the most important features of Kadi4Mat. If you want to pause the tour, you can simply close it and continue it later on this page by clicking on {{-em_open}}Continue tour{{-em_close}}.', {em_open: '<em>', em_close: '</em>'}),
      },
      {
        id: 'interactions',
        clickable: true,
        content: $t('Some steps in this tour allow interacting with the highlighted content. In these cases, the icon in the bottom left corner will be displayed in the current step.'),
      },
      {
        id: 'navbar-left',
        attach: true,
        content: $t('Kadi4Mat provides different types of resources for recording, organizing and sharing data and metadata. Clicking on a resource type will lead to a corresponding overview page. More details about these resources will be explained later.'),
      },
      {
        id: 'navbar-right',
        attach: true,
        content: $t('This part of the navigation bar can be used to quickly create and find resources. It also provides access to various informational pages, including a detailed help page, as well as to your profile, your created/deleted resources and personal settings.'),
      },
      {
        id: 'content',
        attach: true,
        elem: '#base-content',
        content: $t('The home page itself provides quick access to the latest updates of different resources as well as favorited resources and saved searches, if applicable. Some aspects of this page are customizable via the user preferences in the personal settings.'),
      },
      {
        id: 'footer',
        attach: true,
        content: $t('Finally, the most important links as well as a toggle to change the current language can be found in the navigation footer.'),
      },
      {
        id: 'navbar-records',
        attach: true,
        clickable: true,
        content: $t('The remainder of this tour will primarily focus on the so-called records, as these are the basic and most important components of Kadi4Mat. Once your are ready, navigate to the record overview page via the highlighted link.'),
      },
    ],
  },
  {
    id: 'records',
    header: $t('Records'),
    steps: [
      {
        id: 'records',
        content: $t('Records can represent any kind of digital or digitalized object, e.g. arbitrary research data, samples, experimental devices or even individual processing steps. They consist of metadata that can either stand alone or be linked to any number of corresponding data.'),
      },
      {
        id: 'search',
        attach: true,
        elem: '#base-content',
        content: $t('On this overview page, existing records can be searched via a powerful search and filter interface. The overview pages of other resource types look similar for the most part.'),
      },
      {
        id: 'saved-search',
        attach: true,
        content: $t('After performing a search, the currently applied queries and filters can also be saved for later. A corresponding shortcut will be created on the home page automatically.'),
      },
    ],
  },
];

if (kadi.globals.canCreateRecords) {
  tour[1].steps.push({
    id: 'new-record',
    attach: true,
    clickable: true,
    content: $t('New records can also be created here. Once your are ready to do so, navigate to the record creation page via the highlighted button.'),
  });

  tour.push({
    id: 'new-record',
    header: $t('New record'),
    steps: [
      {
        id: 'introduction',
        content: $t('The following steps show how to create a new record and how records relate to other resource types.'),
      },
      {
        id: 'metadata',
        attach: true,
        content: $t('When creating a new record, its metadata has to be specified first. In this tour, the focus is on some of the basic as well as the generic metadata of a record.'),
      },
      {
        id: 'metadata-basics',
        attach: true,
        clickable: true,
        content: $t('In the basic metadata highlighted here, only the title and identifier are required, but try filling out all of the highlighted fields regardless. The identifier uniquely identifies records across Kadi4Mat in a human-readable manner and is based on the entered title by default.'),
      },
      {
        id: 'metadata-extras',
        attach: true,
        clickable: true,
        content: $t('It is also possible to provide generic metadata, usually referred to as {{-em_open}}extra metadata{{-em_close}}. This metadata consists of enhanced key-value pairs of different types (e.g. for textual, numerical or even nested values), allowing the specification of arbitrary, application-specific information. Try entering some metadata using the highlighted editor.', {em_open: '<em>', em_close: '</em>'}),
      },
      {
        id: 'settings',
        attach: true,
        content: $t('While creating new records, it is also possible to directly provide various additional settings instead of doing so after creating the record.'),
      },
      {
        id: 'settings-collections',
        attach: true,
        content: $t('For example, it is possible to directly link the newly created record with one or more collections. Collections represent logical groupings (e.g. projects, simulation studies or experiments) of multiple records or even other collections and can be created similarly to records.'),
      },
      {
        id: 'settings-records',
        attach: true,
        content: $t('Additionally, the newly created record can directly be linked with one or more existing records, specifying their relationship.'),
      },
      {
        id: 'settings-permissions',
        attach: true,
        content: $t('Finally, access permissions can directly be granted for the newly created record, either for individual users or groups of multiple users. The latter can be created similarly to records.'),
      },
      {
        id: 'import',
        attach: true,
        content: $t('Note that it is also possible to import record metadata from a file or to select an existing template when creating a new record. Templates facilitate the creation of records and other resources via the web interface and can be created similarly to records.'),
      },
      {
        id: 'submit',
        attach: true,
        clickable: true,
        content: $t('Once you are finished with entering the desired metadata of your record, try creating it by clicking on the highlighted button. If something goes wrong, fix any invalid metadata and try again.'),
      },
    ],
  });

  tour.push({
    id: 'files',
    header: $t('Files'),
    steps: [
      {
        id: 'add-files',
        attach: true,
        clickable: true,
        content: $t('This is where you may add files to the newly created record. Besides uploading local files, some file types can also be created directly via the web interface by clicking on the different tabs at the top of the highlighted content.'),
      },
      {
        id: 'back-to-record',
        attach: true,
        clickable: true,
        content: $t('Once you are done, navigate back to the files overview page of this record by clicking on the highlighted link.'),
      },
    ],
  });
} else {
  tour[1].steps.push({
    id: 'new-record',
    content: $t('Unfortunately, your current system role does not allow creating new records. In order to continue this tour, please navigate to the overview page of an existing record instead, if possible.'),
  });
}

tour.push({
  id: 'record',
  header: $t('Record'),
  steps: [
    {
      id: 'files',
      attach: true,
      elem: '[data-tour="record"]',
      content: $t('This is the overview page of this record, divided into different sections. Each section can be accessed by clicking on the corrsponding tab at the top of the highlighted content. On the current section, an overview of the files of this record are shown. Note that each file has their own overview page as well.'),
    },
    {
      id: 'overview',
      attach: true,
      elem: '[data-tour="record"]',
      content: $t('This section gives a general overview of this record\'s metadata. The buttons at the top of the higlighted content provide different ways to interact with this record, e.g. editing or exporting it. Most sections provide similar buttons, depending on the respective content.'),
    },
    {
      id: 'links',
      attach: true,
      elem: '[data-tour="record"]',
      content: $t('This section focuses on the links of this record with other resources, namely collections and other records. Unless you already specified linked resources while creating this record, no contents will be shown here yet.'),
    },
    {
      id: 'permissions',
      attach: true,
      elem: '[data-tour="record"]',
      content: $t('This section focuses on the access permissions that have been granted for this record. Unless you already specified additional users or groups while creating this record, only your own user will appear here for now.'),
    },
    {
      id: 'revisions',
      attach: true,
      elem: '[data-tour="record"]',
      content: $t('Finally, this section provides an overview of the change history of a record\'s metadata and the corresponding file metadata.'),
    },
    {
      id: 'conclusion',
      content: $t('This concludes the basic tour of Kadi4Mat. Remember to check the help page for additional information, including more details about the generic record metadata, the application programming interface that Kadi4Mat provides, and more.'),
    },
  ],
});

export default tour;
