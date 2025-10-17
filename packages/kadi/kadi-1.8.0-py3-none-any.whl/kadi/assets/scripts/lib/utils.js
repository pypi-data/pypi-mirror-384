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

export default {
  /** Add an item to an array at the specified position. */
  addToArray(array, item, index = null) {
    if (index !== null) {
      array.splice(index + 1, 0, item);
    } else {
      array.push(item);
    }
  },

  /** Wrap a value inside an array if the given value is not an array already. */
  asArray(value) {
    if (!kadi.utils.isArray(value)) {
      return [value];
    }
    return value;
  },

  /** Encode an arbitrary unicode string into Base64. */
  b64EncodeUnicode(string) {
    return window.btoa(window.encodeURIComponent(string).replace(/%([0-9A-F]{2})/g, (match, p1) => {
      return String.fromCharCode(`0x${p1}`);
    }));
  },

  /** Capitalize a string. */
  capitalize(string) {
    if (string.length === 0) {
      return string;
    }
    return string.charAt(0).toUpperCase() + string.slice(1);
  },

  /** Clamp a numeric value to the inclusive range of the given min and max values. */
  clamp(value, min, max) {
    return Math.min(Math.max(value, min), max);
  },

  /** Perform a shallow check if the contents of two objects are equal. */
  objectsEqual(first, second) {
    const stringify = (object) => JSON.stringify(Object.entries(object).sort());
    return stringify(first) === stringify(second);
  },

  /** Perform a deep copy of an object or array consisting of JSON (de)serializable values. */
  deepClone(value) {
    return JSON.parse(JSON.stringify(value));
  },

  /**
   * Create a human-readable, localized file size from a given amount of bytes.
   *
   * Based on Jinja's 'filesizeformat' filter.
   */
  filesize(bytes) {
    const prefixes = ['kB', 'MB', 'GB', 'TB', 'PB'];
    const numBytes = Number.parseInt(bytes, 10);
    const base = 1_000;

    if (numBytes === 1) {
      return '1 Byte';
    } else if (numBytes < base) {
      return `${numBytes} Bytes`;
    }

    let unit = 1;
    let index = 0;

    for (; index < prefixes.length; index++) {
      unit = base ** (index + 2);

      if (numBytes < unit) {
        break;
      }
    }

    if (index >= prefixes.length) {
      index = prefixes.length - 1;
    }

    const formattedSize = kadi.utils.formatNumber(base * numBytes / unit, {maximumFractionDigits: 1});
    return `${formattedSize} ${prefixes[index]}`;
  },

  /** Create a localized string based on a given number. */
  formatNumber(number, options = {}) {
    return Number(number).toLocaleString(kadi.globals.locale, options);
  },

  /** Get a nested property of an object given a string specifying the properties separated by dots. */
  getProp(object, property) {
    const props = property.split('.');
    let result = object;

    for (const prop of props) {
      result = result[prop];
    }
    return result;
  },

  /** Get one or multiple values of a search parameter of the current URL. */
  getSearchParam(param, getAll = false, url = window.location) {
    const wrappedUrl = new URL(url);
    const searchParams = new URLSearchParams(wrappedUrl.search);

    if (getAll) {
      return searchParams.getAll(param);
    }
    return searchParams.get(param);
  },

  /** Check if the current URL contains a certain search parameter. */
  hasSearchParam(param, url = window.location) {
    const wrappedUrl = new URL(url);
    const searchParams = new URLSearchParams(wrappedUrl.search);

    return searchParams.has(param);
  },

  /** Insert a string at a given position inside another string. */
  insertString(string, index, toInsert) {
    if (index > 0) {
      return `${string.slice(0, index)}${toInsert}${string.slice(index)}`;
    }
    return toInsert + string;
  },

  /** Check if a variable is an array. */
  isArray(value) {
    return Array.isArray(value);
  },

  /** Check if the current page is on full screen. */
  isFullscreen() {
    return document.fullscreenElement !== null;
  },

  /** Check if a string represents a valid HTTP URL. */
  isHttpUrl(value) {
    try {
      const url = new URL(value);

      if (['http:', 'https:'].includes(url.protocol)) {
        return true;
      }
    } catch {
      return false;
    }

    return false;
  },

  /** Check if the type of an extra metadata entry is nested. */
  isNestedType(type) {
    return ['dict', 'list'].includes(type);
  },

  /** Check if a variable is an object. */
  isObject(value) {
    return value !== null && typeof value === 'object' && !kadi.utils.isArray(value);
  },

  /** Check if a string value is quoted, i.e. surrounded by double quotes. */
  isQuoted(string) {
    return string.startsWith('"') && string.endsWith('"') && string.length >= 2;
  },

  /** Normalize all and strip surrounding whitespaces in a string. */
  normalize(string) {
    return string.replace(/\s+/g, ' ').trim();
  },

  /** Paginate an arrary given a page and the amount of items per page. */
  paginateArray(array, page, perPage) {
    const start = (page - 1) * perPage;
    const end = start + perPage;
    return array.slice(start, end);
  },

  /** Return a pretty type name based on the type of an extra metadata. */
  prettyTypeName(type) {
    switch (type) {
      case 'str': return 'string';
      case 'int': return 'integer';
      case 'bool': return 'boolean';
      case 'dict': return 'dictionary';
      default: return type;
    }
  },

  /**
   * Generate a (not cryprographically secure) random alphanumeric string with a given length.
   *
   * Note that the first character is guaranteed to be a letter, so the resulting string is always safe to use and query
   * as an element ID.
   */
  randomAlnum(length = 16) {
    const letters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz';
    const chars = `${letters}0123456789`;

    let result = '';

    for (let i = 0; i < length; i++) {
      if (i === 0) {
        result += letters[Math.floor(Math.random() * letters.length)];
      } else {
        result += chars[Math.floor(Math.random() * chars.length)];
      }
    }

    return result;
  },

  /** Remove all occurences of a given item from an array. */
  removeFromArray(array, item) {
    let index = array.indexOf(item);

    while (index >= 0) {
      array.splice(index, 1);
      index = array.indexOf(item);
    }
  },

  /** Remove a single or all search parameter values of the current URL and return the new URL. */
  removeSearchParam(param, value = null, url = window.location) {
    const wrappedUrl = new URL(url);
    const searchParams = new URLSearchParams(wrappedUrl.search);

    if (value === null) {
      searchParams.delete(param);
    } else {
      searchParams.delete(param, value);
    }

    wrappedUrl.search = searchParams;
    return wrappedUrl;
  },

  /**
   * Replace the current URL while retaining the old navigation history.
   *
   * Also globally dispatches a custom 'kadi-replace-state' event in order to react to state changes.
   */
  replaceState(url) {
    window.history.replaceState(null, '', url);
    window.dispatchEvent(new Event('kadi-replace-state'));
  },

  /** Scroll an element into the view using a specific alignment relative to it. */
  scrollIntoView(element, alignment = 'center') {
    if (alignment === 'top') {
      element.scrollIntoView(true);

      if (window.innerWidth >= 768) {
        // Take the potentially fixed navigation header into account, based on the MD Bootstrap breakpoint.
        window.scrollBy(0, element.getBoundingClientRect().top - 66);
      }
    } else if (alignment === 'bottom') {
      element.scrollIntoView(false);
    } else {
      element.scrollIntoView(false);
      const viewportRatio = element.getBoundingClientRect().top / window.innerHeight;
      window.scrollBy(0, (viewportRatio - 0.5) * window.innerHeight);
    }
  },

  /** Replace or append values to a search parameter of the current URL and return the new URL. */
  setSearchParam(param, value, replace = true, url = window.location) {
    const wrappedUrl = new URL(url);
    const searchParams = new URLSearchParams(wrappedUrl.search);

    if (replace) {
      searchParams.set(param, value);
    } else {
      searchParams.append(param, value);
    }

    wrappedUrl.search = searchParams;
    return wrappedUrl;
  },

  /** Sleep for the given amount of milliseconds. */
  sleep(ms) {
    return new Promise((resolve) => window.setTimeout(resolve, ms));
  },

  /** Convert a value to scientific notation if it is a number above or below a certain value threshold. */
  toExponentional(value) {
    if (typeof value === 'number' && value !== 0 && (Math.abs(value) >= 10_000 || Math.abs(value) <= 0.0001)) {
      return value.toExponential();
    }

    return value;
  },

  /** Toggle a full screen view of the current page for the given element. */
  toggleFullscreen(element) {
    if (kadi.utils.isFullscreen()) {
      return document.exitFullscreen();
    }
    return element.requestFullscreen();
  },

  /** Truncate a string based on a given length. */
  truncate(string, length) {
    if (string.length > length) {
      return `${string.substring(0, length)}...`;
    }
    return string;
  },
};
