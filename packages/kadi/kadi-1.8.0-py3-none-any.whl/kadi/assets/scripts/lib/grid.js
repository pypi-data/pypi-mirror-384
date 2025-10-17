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

class Column {
  constructor(id, size = 1, offset = 0, isPlaceholder = true) {
    this.id = id;
    this.size = size;
    this.offset = offset;
    this.isPlaceholder = isPlaceholder;
  }

  static from(other) {
    return other === null
      ? new Column(window.crypto.randomUUID())
      : new Column(other.id, other.size, other.offset || 0, other.isPlaceholder || false);
  }

  toJSON() {
    return {
      id: this.id,
      size: this.size,
      offset: this.offset,
    };
  }
}

class Row {
  constructor(id, columns = []) {
    this.id = id;
    this.columns = columns;
  }

  static from(other) {
    return new Row(other.id, other.columns.filter((column) => column).map((column) => Column.from(column)));
  }

  get maxColumnCount() {
    return 12;
  }

  get minColumnSize() {
    return 3;
  }

  fillWithPlaceholders() {
    const missingColumnCount = this.columns.reduce((sum, column) => sum - column.size, this.maxColumnCount);

    for (let i = 0; i < missingColumnCount; ++i) {
      this.columns.push(new Column(window.crypto.randomUUID()));
    }
  }

  canInsertColumnAt(index) {
    const count
      = this._countPlaceholdersForward(index + 1)
      + this._countPlaceholdersBackward(index - 1)
      + 1;

    return count >= this.minColumnSize;
  }

  insertColumnAt(index) {
    let columnIndex = index;

    const forwardSpace = this._countPlaceholdersForward(index);

    // If there is not enough space in front of the column move it back until there is.
    if (forwardSpace < this.minColumnSize) {
      const newIndex = columnIndex - (this.minColumnSize - forwardSpace);
      [this.columns[columnIndex], this.columns[newIndex]] = [this.columns[newIndex], this.columns[columnIndex]];

      columnIndex = newIndex;
    }

    const column = this.columns[columnIndex];
    column.isPlaceholder = false;
    column.size = 1;

    for (let i = 1; i < this.minColumnSize; ++i) {
      this.growColumn(column);
    }

    return column;
  }

  removeColumn(column) {
    const columnIndex = this._findColumnIndex(column);

    // Refill the space.
    for (let i = 0; i < column.size; ++i) {
      this.columns.splice(columnIndex + 1, 0, new Column(window.crypto.randomUUID()));
    }

    // Remove also the original column to provide a clean data set.
    this.columns.splice(columnIndex, 1);
  }

  growColumn(column, direction = 'right') {
    if (column.size === this.maxColumnCount) {
      return;
    }

    const columnIndex = this._findColumnIndex(column);
    let freeColumns = 0;

    if (direction === 'right') {
      freeColumns = this._countPlaceholdersForward(columnIndex + 1);
    } else if (direction === 'left') {
      freeColumns = this._countPlaceholdersBackward(columnIndex - 1);
    }

    if (freeColumns === 0) {
      return;
    }

    this.columns.splice(columnIndex + (direction === 'right' ? 1 : -1), 1);
    ++column.size;
  }

  shrinkColumn(column, direction) {
    if (column.size === this.minColumnSize) {
      return;
    }

    const spliceDirection = direction === 'right' ? 1 : 0;
    this.columns.splice(this._findColumnIndex(column) + spliceDirection, 0, new Column(window.crypto.randomUUID()));

    --column.size;
  }

  toJSON() {
    this._recalcColumnOffsets();

    return {
      id: this.id,
      columns: this.columns.filter((column) => !column.isPlaceholder).map((column) => column.toJSON()),
    };
  }

  restore() {
    const restoredColumns = [];

    this.columns.forEach((column) => {
      // Add placeholders before the column.
      for (let j = 0; j < column.offset; ++j) {
        restoredColumns.push(new Column(window.crypto.randomUUID()));
      }

      // Add the column itself.
      restoredColumns.push(column);
    });

    this.columns = restoredColumns;

    // Fill the remaining space.
    this.fillWithPlaceholders();
  }

  _countPlaceholdersForward(begin) {
    let count = 0;

    for (let i = begin; i < this.columns.length; ++i) {
      if (this.columns[i].isPlaceholder && this.columns[i].size > 0) {
        ++count;
      } else {
        break;
      }
    }

    return count;
  }

  _countPlaceholdersBackward(begin) {
    let count = 0;

    for (let i = begin; i >= 0; --i) {
      if (this.columns[i].isPlaceholder && this.columns[i].size > 0) {
        ++count;
      } else {
        break;
      }
    }

    return count;
  }

  _findColumnIndex(column) {
    return this.columns.findIndex((c) => c.id === column.id);
  }

  _recalcColumnOffsets() {
    let currentOffset = 0;

    this.columns.forEach((column) => {
      column.offset = currentOffset;
      currentOffset += column.size;

      if (!column.isPlaceholder) {
        currentOffset = 0;
      }
    });
  }
}

class Layout {
  constructor(id, rows = []) {
    this.id = id;
    this.rows = rows;
  }

  static from(other) {
    return new Layout(other.id, other.rows.map((other) => Row.from(other)));
  }

  addRow() {
    const row = new Row(window.crypto.randomUUID());
    row.fillWithPlaceholders();

    this.rows.push(row);
  }

  removeRow(row) {
    const rowIndex = this._findRowIndexById(row.id);

    if (rowIndex < 0) {
      return;
    }

    this.rows.splice(rowIndex, 1);
  }

  toJSON() {
    return {
      id: this.id,
      rows: this.rows.map((row) => row.toJSON()),
    };
  }

  restore() {
    this.rows.forEach((row) => row.restore());
  }

  _findRowIndexById(rowId) {
    return this.rows.findIndex((row) => row.id === rowId);
  }
}

export {Layout as GridLayout, Row as GridRow, Column as GridColumn};
