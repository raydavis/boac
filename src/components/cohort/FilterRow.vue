<template>
  <div
    v-if="showRow"
    :class="{'pt-2': !isExistingFilter}"
    class="d-flex flex-wrap">
    <div
      v-if="isExistingFilter"
      :id="`existing-name-${index}`"
      class="existing-filter-name p-2">
      <span class="sr-only">Filter name:</span> {{ filter.label.primary }}
    </div>
    <div
      v-if="isModifyingFilter && !isExistingFilter"
      :id="filterRowPrimaryDropdownId(filterRowIndex)"
      class="filter-row-column-01 mt-1 pr-2">
      <b-dropdown
        id="new-filter-button"
        toggle-class="dd-override"
        variant="link"
        no-caret>
        <template slot="button-content">
          <div class="d-flex dropdown-width justify-content-between text-dark">
            <div v-if="filter.label"><span class="sr-only">Filter: </span>{{ filter.label.primary || 'New Filter' }}</div>
            <div v-if="!filter.label"><span class="sr-only">Select a </span>New Filter</div>
            <div class="ml-2">
              <font-awesome :icon="isMenuOpen ? 'angle-up' : 'angle-down'" class="menu-caret" />
            </div>
          </div>
        </template>
        <div
          v-for="(category, mIndex) in menu"
          :key="mIndex"
          :aria-labelledby="'filter-option-group-header-' + mIndex"
          role="group">
          <b-dropdown-header :id="'filter-option-group-header-' + mIndex" class="sr-only">
            Filter option group {{ mIndex + 1 }} of {{ menu.length }}
          </b-dropdown-header>
          <b-dropdown-item
            v-for="subCategory in category"
            :id="`dropdown-primary-menuitem-${subCategory.key}-${filterRowIndex}`"
            :key="subCategory.key"
            :aria-disabled="subCategory.disabled"
            :disabled="subCategory.disabled"
            @click="onSelectFilter(subCategory)"
            @focusin.prevent.stop
            @mouseover.prevent.stop
            class="dropdown-item">
            <span
              :class="{
                'font-weight-light pointer-default text-muted': subCategory.disabled,
                'font-weight-normal text-dark': !subCategory.disabled
              }"
              class="font-size-16">{{ subCategory.label.primary }}</span>
          </b-dropdown-item>
          <hr v-if="mIndex !== (menu.length - 1)" class="dropdown-divider">
        </div>
      </b-dropdown>
    </div>
    <div v-if="!isModifyingFilter">
      <span class="sr-only">Selected filter value: </span>
      <span v-if="isUX('dropdown')">{{ getDropdownSelectedLabel() }}</span>
      <span v-if="isUX('range')">{{ rangeMinLabel() }} {{ rangeMaxLabel() }}</span>
    </div>
    <div
      v-if="isModifyingFilter"
      class="filter-row-column-02 mt-1">
      <div
        v-if="isUX('dropdown')"
        :id="`filter-row-dropdown-secondary-${filterRowIndex}`">
        <b-dropdown
          toggle-class="dd-override"
          variant="link"
          no-caret>
          <template slot="button-content">
            <div class="d-flex dropdown-width justify-content-between text-secondary">
              <div v-if="filter.value">
                <span class="sr-only">Selected value is </span>
                <span v-if="isUX('dropdown')">{{ getDropdownSelectedLabel() }}</span>
                <span v-if="isUX('range')">{{ rangeMinLabel() }} {{ rangeMaxLabel() }}</span>
              </div>
              <div v-if="!filter.value">Choose...<span class="sr-only"> a filter value option</span></div>
              <div class="ml-2">
                <font-awesome :icon="isMenuOpen ? 'angle-up' : 'angle-down'" class="menu-caret" />
              </div>
            </div>
          </template>
          <div v-for="option in filter.options" :key="option.key">
            <b-dropdown-item
              v-if="option.value !== 'divider'"
              :id="`${filter.label.primary}-${option.value}`"
              :aria-disabled="option.disabled"
              :disabled="option.disabled"
              @click="updateDropdownValue(option)"
              @focusin.prevent.stop
              @mouseover.prevent.stop
              class="dropdown-item">
              <span
                :class="{
                  'font-weight-light pointer-default text-muted': option.disabled,
                  'font-weight-normal text-dark': !option.disabled
                }"
                class="font-size-16">{{ option.name }}</span>
            </b-dropdown-item>
            <hr v-if="option.value === 'divider'" class="dropdown-divider">
          </div>
        </b-dropdown>
      </div>
      <div v-if="isUX('range')" class="filter-range-container">
        <div class="filter-range-label-min">
          {{ rangeMinLabel() }}
        </div>
        <div>
          <span
            :id="isExistingFilter ? `filter-range-min-${index}-label` : 'filter-range-min-label'"
            class="sr-only">beginning of range</span>
          <input
            :id="idRangeMin"
            v-model="range.min"
            :aria-labelledby="isExistingFilter ? `filter-range-min-${index}-label` : 'filter-range-min-label'"
            :maxlength="rangeInputSize()"
            :size="rangeInputSize()"
            class="filter-range-input" />
        </div>
        <div class="filter-range-label-max">
          {{ rangeMaxLabel() }}
        </div>
        <div>
          <span
            :id="isExistingFilter ? `filter-range-max-${index}-label` : 'filter-range-max-label'"
            class="sr-only">end of range</span>
          <input
            :id="idRangeMax"
            v-model="range.max"
            :aria-labelledby="isExistingFilter ? `filter-range-max-${index}-label` : 'filter-range-max-label'"
            :maxlength="rangeInputSize()"
            :size="rangeInputSize()"
            class="filter-range-input" />
        </div>
        <div class="sr-only" aria-live="polite">{{ errorPerRangeInput }}</div>
        <b-popover
          v-if="size(errorPerRangeInput)"
          :show="true"
          :target="isExistingFilter ? `filter-range-min-${index}` : 'filter-range-min'"
          placement="top">
          <span class="has-error">{{ errorPerRangeInput }}</span>
        </b-popover>
      </div>
    </div>
    <div v-if="!isExistingFilter" class="filter-row-column-03 mt-1 pl-0">
      <b-btn
        id="unsaved-filter-add"
        v-if="showAdd"
        @click="onClickAddButton()"
        class="btn-primary-color-override ml-2"
        variant="primary"
        aria-label="Add this new filter to the search criteria">
        Add
      </b-btn>
    </div>
    <div
      v-if="isModifyingFilter && get(filter, 'type.ux') && !isExistingFilter"
      class="filter-row-column-04">
      <b-btn
        id="unsaved-filter-reset"
        @click="reset()"
        class="p-0"
        variant="link"
        aria-label="Cancel this filter selection">
        Cancel
      </b-btn>
    </div>
    <div v-if="isOwnedByCurrentUser && isExistingFilter" class="ml-auto p-2">
      <div v-if="!isModifyingFilter" class="d-flex flex-row">
        <span v-if="!isUX('boolean')">
          <b-btn
            :id="`edit-added-filter-${index}`"
            :aria-label="`Edit ${filter.label.primary} filter (row ${index})`"
            @click="onClickEditButton()"
            class="btn-cohort-added-filter pr-1"
            variant="link"
            size="sm">
            Edit
          </b-btn> |
        </span>
        <b-btn
          :id="`remove-added-filter-${index}`"
          :aria-label="`Remove this ${filter.label.primary} filter`"
          @click="remove()"
          class="btn-cohort-added-filter pl-2 pr-0"
          variant="link"
          size="sm">
          Remove
        </b-btn>
      </div>
      <div v-if="isModifyingFilter" class="d-flex flex-row">
        <b-btn
          :id="`update-added-filter-${index}`"
          :aria-label="`Update this ${filter.label.primary} filter`"
          :disabled="disableUpdateButton"
          @click="onClickUpdateButton()"
          class="btn-primary-color-override"
          variant="primary"
          size="sm">
          Update
        </b-btn>
        <b-btn
          :id="`cancel-edit-added-filter-${index}`"
          @click="onClickCancelEdit()"
          class="btn-cohort-added-filter"
          variant="link"
          aria-label="Cancel update"
          size="sm">
          Cancel
        </b-btn>
      </div>
    </div>
  </div>
</template>

<script>
import CohortEditSession from '@/mixins/CohortEditSession';
import Context from '@/mixins/Context';
import UserMetadata from '@/mixins/UserMetadata';
import Util from '@/mixins/Util';

export default {
  name: 'FilterRow',
  mixins: [CohortEditSession, Context, UserMetadata, Util],
  props: {
    index: Number
  },
  data: () => ({
    disableUpdateButton: false,
    errorPerRangeInput: undefined,
    filter: undefined,
    isExistingFilter: undefined,
    isMenuOpen: false,
    isModifyingFilter: undefined,
    range: {
      min: undefined,
      max: undefined
    },
    showAdd: false,
    showRow: true,
    valueOriginal: undefined
  }),
  computed: {
    filterRowIndex() {
      return this.isExistingFilter ? this.index : 'new';
    },
    idRangeMax() {
      return this.isExistingFilter
        ? `filter-range-max-${this.index}`
        : 'filter-range-max';
    },
    idRangeMin() {
      return this.isExistingFilter
        ? `filter-range-min-${this.index}`
        : 'filter-range-min';
    }
  },
  watch: {
    editMode(newEditMode) {
      // Reset the current filter-row if an edit session is initiated elsewhere.
      if (this.isNil(newEditMode)) {
        // Nothing is being edited. Let's make sure this row is in default state.
        this.reset();
        this.showRow = true;
      } else if (newEditMode === 'add') {
        if (this.isExistingFilter) {
          // User is adding a new filter so other rows, per existing filters, are put back in default state.
          this.reset();
        }
      } else if (newEditMode.match('edit-[0-9]+')) {
        if (this.isExistingFilter) {
          if (newEditMode !== `edit-${this.index}`) {
            // We do not allow two rows to be in edit mode simultaneously. In this case, some other row is entering edit
            // mode so we effectively click cancel on this row.
            this.reset();
          }
        } else {
          // Reset and then hide this 'New Filter' row because user has clicked to edit an existing filter.
          this.reset();
          this.showRow = false;
        }
      } else if (newEditMode === 'rename') {
        this.reset();
      }
    },
    range: {
      handler(rangeObject) {
        this.disableUpdateButton = false;
        this.errorPerRangeInput = undefined;
        const trimToNil = v => this.isUndefined(v) ? v : this.trim(v) || undefined;
        let min = trimToNil(this.get(rangeObject, 'min'));
        let max = trimToNil(this.get(rangeObject, 'max'));
        const isNilOrNan = v => this.isNil(v) || this.isNaN(v);
        if (this.filter.validation === 'gpa') {
          min = min && parseFloat(min);
          max = max && parseFloat(max);
          const isDefinedAndInvalid = v => (this.isNumber(v) && v < 0 || v > 4) || this.isNaN(v);
          if (isDefinedAndInvalid(min) || isDefinedAndInvalid(max)) {
            this.errorPerRangeInput = 'GPA must be a number in the range 0 to 4.';
          } else if (this.isNumber(min) && this.isNumber(max) && min > max) {
            this.errorPerRangeInput = 'GPA inputs must be in ascending order.';
          }
          this.disableUpdateButton = !!this.errorPerRangeInput || isNilOrNan(min) || isNilOrNan(max) || min > max;
        } else if (this.filter.validation === 'char') {
          if (min && max && min > max) {
            this.disableUpdateButton = true;
            this.errorPerRangeInput = 'Letters must be in ascending order.';
          } else {
            this.disableUpdateButton = isNilOrNan(min) || isNilOrNan(max) || min > max;
          }
        } else if (this.filter.validation) {
          this.disableUpdateButton = true;
          this.errorPerRangeInput = `Unrecognized range type: ${this.filter.validation}`;
        }
        this.showAdd = !this.errorPerRangeInput && !isNilOrNan(min) && !isNilOrNan(max);
      },
      deep: true
    }
  },
  created() {
    this.reset();
    this.valueOriginal = this.filter && this.cloneDeep(this.filter.value);
  },
  methods: {
    filterRowPrimaryDropdownId: index => `filter-row-dropdown-primary-${index}`,
    filterRowSecondaryDropdownId: index => `filter-row-dropdown-secondary-${index}`,
    formatGPA(value) {
      // Prepend zero in case input is, for example, '.2'. No harm done if input has a leading zero.
      const gpa = '0' + this.trim(value);
      return parseFloat(gpa).toFixed(3);
    },
    getDropdownSelectedLabel() {
      return this.get(this.find(this.filter.options, ['value', this.filter.value]), 'name');
    },
    isUX(type) {
      return this.get(this.filter, 'type.ux') === type;
    },
    onClickAddButton() {
      switch (this.get(this.filter, 'type.ux')) {
        case 'dropdown':
          this.alertScreenReader(`Added ${this.filter.label.primary} filter with value ${this.getDropdownSelectedLabel()}`);
          break;
        case 'boolean':
          this.alertScreenReader(`Added ${this.filter.label.primary}`);
          this.filter.value = true;
          break;
        case 'range':
          this.alertScreenReader(`Added ${this.filter.label.primary} filter, ${this.range.min} to ${this.range.max}`);
          this.filter.value = {
            min: this.filter.validation === 'gpa' ? this.formatGPA(this.range.min) : this.range.min.toUpperCase(),
            max: this.filter.validation === 'gpa' ? this.formatGPA(this.range.max) : this.range.max.toUpperCase()
          };
          this.range.min = this.range.max = undefined;
          break;
      }
      this.addFilter(this.filter);
      this.reset();
      this.putFocusNewFilterDropdown();
      this.gaCohortEvent({
        id: this.cohortId,
        name: this.cohortName || '',
        action: this.screenReaderAlert
      });
    },
    onClickCancelEdit() {
      this.alertScreenReader('Canceled');
      this.isModifyingFilter = false;
      this.setEditMode(null);
      this.putFocusNewFilterDropdown();
    },
    onClickEditButton() {
      this.disableUpdateButton = false;
      if (this.isUX('dropdown')) {
        const category = this.find(this.flatten(this.menu), ['key', this.filter.key]);
        this.filter.options = category.options;
      } else if (this.isUX('range')) {
        this.range.min = this.filter.value.min;
        this.range.max = this.filter.value.max;
      }
      this.isModifyingFilter = true;
      this.setEditMode(`edit-${this.index}`);
      this.putFocusSecondaryDropdown();
      this.alertScreenReader(`Begin edit of ${this.filter.label.primary} filter`);
    },
    onClickUpdateButton() {
      if (this.isUX('range')) {
        const isGPA = this.filter.validation === 'gpa';
        this.filter.value = {
          min: isGPA ? this.formatGPA(this.range.min) : this.range.min,
          max: isGPA ? this.formatGPA(this.range.max) : this.range.max
        };
      }
      this.updateExistingFilter({index: this.index, updatedFilter: this.filter}).then(() => {
        this.isModifyingFilter = false;
        this.setEditMode(null);
        this.alertScreenReader(`${this.filter.label.primary} filter updated`);
        this.gaCohortEvent({
          id: this.cohortId,
          name: this.cohortName,
          action: this.screenReaderAlert
        });
      });
    },
    onSelectFilter(filter) {
      this.filter = this.cloneDeep(filter);
      this.showAdd = filter.type.ux === 'boolean';
      this.alertScreenReader(`${filter.label.primary} selected`);
      switch (filter.type.ux) {
        case 'dropdown':
          this.putFocusSecondaryDropdown();
          break;
        case 'boolean':
          this.putFocusNextTick('unsaved-filter-add');
          break;
        case 'range':
          this.putFocusNextTick(this.idRangeMin);
          break;
      }
    },
    putFocusNewFilterDropdown() {
      this.putFocusNextTick(this.filterRowPrimaryDropdownId('new'), 'button');
    },
    putFocusSecondaryDropdown() {
      this.putFocusNextTick(
        this.filterRowSecondaryDropdownId(this.filterRowIndex),
        'button'
      );
    },
    rangeInputSize() {
      let maxLength = undefined;
      if (this.filter.validation === 'char') {
        maxLength = 1;
      } else if (this.filter.validation === 'gpa') {
        maxLength = 5;
      }
      return maxLength;
    },
    rangeMaxLabel() {
      let snippet = undefined;
      if (this.isModifyingFilter) {
        snippet = this.filter.label.range[1];
      } else {
        const min = this.get(this.filter, 'value.min');
        const max = this.get(this.filter, 'value.max');
        const minEqualsMax = !this.isNil(min) && min === max;
        const labels = this.get(this.filter.label, 'range');
        snippet = minEqualsMax ? '' : `${labels[1]} ${max}`;
      }
      return snippet;
    },
    rangeMinLabel() {
      let snippet = undefined;
      if (this.isModifyingFilter) {
        snippet = this.filter.label.range[0];
      } else {
        const min = this.get(this.filter, 'value.min');
        const max = this.get(this.filter, 'value.max');
        const minEqualsMax = !this.isNil(min) && min === max;
        const labels = this.get(this.filter.label, 'range');
        snippet = minEqualsMax ? this.get(this.filter.label, 'rangeMinEqualsMax') + ' ' + min : `${labels[0]} ${min}`;
      }
      return snippet;
    },
    remove() {
      this.alertScreenReader(`${this.filter.label.primary} filter removed`);
      this.removeFilter(this.index);
      this.setEditMode(null);
      this.putFocusNewFilterDropdown();
      this.gaCohortEvent({
        id: this.cohortId,
        name: this.cohortName || '',
        action: this.screenReaderAlert
      });
    },
    reset() {
      this.disableUpdateButton = false;
      this.showAdd = false;
      this.range = this.mapValues(this.range, () => undefined);
      if (this.isNil(this.index)) {
        this.filter = {};
        this.isExistingFilter = false;
        this.isModifyingFilter = true;
      } else {
        this.filter = this.cloneDeep(this.filters[this.index]);
        this.isExistingFilter = true;
        this.isModifyingFilter = false;
      }
      this.putFocusNewFilterDropdown();
    },
    updateDropdownValue(option) {
      if (option) {
        this.filter.value = option.value;
        this.showAdd = true;
        this.putFocusNextTick('unsaved-filter-add');
        this.alertScreenReader(`${option.name} selected`);
      }
    }
  }
};
</script>

<style scoped>
.btn-cohort-added-filter {
  text-transform: uppercase;
  font-size: 0.8em;
  padding: 4px 1px 5px 5px;
}
.filter-row-column-01 .b-dropdown,
.filter-row-column-02 .b-dropdown {
  background-color: #f3f3f3;
  border: 1px solid #ccc;
  border-radius: 4px;
  color: #000;
  height: 42px;
  text-align: left;
  vertical-align: middle;
  white-space: nowrap;
}
.dropdown-item {
  font-size: 14px;
  padding-top: 3px;
}
.filter-row-column-01 {
  border-left: 6px solid #3b7ea5;
  flex: 0 0 240px;
}
.filter-row-column-01 .dropdown-item {
  width: 330px;
}
.filter-row-column-01 .dropdown-width {
  width: 260px;
}
.filter-row-column-02 {
  flex: 0;
}
.filter-row-column-02 .dropdown-item {
  width: 340px;
}
.filter-row-column-02 .dropdown-width {
  width: 320px;
}
.filter-row-column-03 {
  flex-basis: auto;
}
.filter-row-column-03 button {
  height: 40px;
  margin-left: 10px;
  width: 80px;
}
.filter-row-column-04 {
  flex: 1;
  vertical-align: middle;
}
.filter-row-column-04 button {
  margin: 8px 0 0 10px;
}
.existing-filter-name {
  width: 260px;
}
.filter-range-container {
  display: flex;
  flex-direction: row;
  padding-right: 15px;
}
.filter-range-label-min {
  padding: 10px 8px 0 0;
}
.filter-range-label-max {
  padding: 10px 8px 0 10px;
}
.filter-range-input {
  border: 2px solid #ccc;
  border-radius: 8px;
  box-sizing: border-box;
  color: #333;
  font-size: 18px;
  padding: 8px 15px 8px 17px;
  text-transform: uppercase;
}
.menu-caret {
  font-size: 22px;
}
.pointer-default {
  cursor: default;
}
</style>
