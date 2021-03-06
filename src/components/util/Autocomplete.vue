<template>
  <div :id="id">
    <b-form-input
      ref="autocompleteInput"
      :id="`${id}-input`"
      v-model="query"
      :class="{'obfuscate-form-input': demoModeBlur && user.inDemoMode}"
      :disabled="disabled"
      :placeholder="placeholder"
      @input="onTextInput"
      @keypress.enter.prevent="onArrowDown"
      @keyup.esc="onEscFormInput"
      @keyup.down="onArrowDown"
      name="autocomplete-name"
      type="text"
      autocomplete="off">
    </b-form-input>
    <div class="dropdown">
      <ul
        ref="autocompleteSuggestions"
        :id="`${id}-suggestions`"
        :class="{'dropdown-menu-open': isOpen, dropdownClass: true}"
        @keyup.down="onArrowDown"
        @keyup.up="onArrowUp"
        @keyup.esc="onEsc"
        aria-expanded="true"
        class="dropdown-menu"
        role="menu"
        tabIndex="0">
        <li
          v-if="isLoading"
          class="dropdown-item">
          <font-awesome icon="spinner" spin />
        </li>
        <li
          v-if="!isLoading && !suggestions.length"
          :id="`${id}-no-results`"
          class="dropdown-item">
          No results.
        </li>
        <li
          v-for="(suggestion, i) in suggestions"
          :key="i">
          <a
            :id="`${id}-suggestion-${i}`"
            :class="{'demo-mode-blur': demoModeBlur && user.inDemoMode}"
            @click="selectSuggestion(suggestion)"
            @keyup.enter="selectSuggestion(suggestion)"
            role="menuitem"
            class="dropdown-item"
            href="#">
            <span v-html="highlightQuery(suggestion.label)"></span>
          </a>
        </li>
      </ul>
    </div>
  </div>
</template>

<script>
import UserMetadata from '@/mixins/UserMetadata';
import Util from '@/mixins/Util';

export default {
  name: 'Autocomplete',
  mixins: [UserMetadata, Util],
  props: {
    demoModeBlur: {
      default: false,
      required: false,
      type: Boolean
    },
    disabled: {
      default: false,
      required: false,
      type: Boolean
    },
    dropdownClass: {
      default: 'autocomplete-dropdown-menu',
      required: false,
      type: String
    },
    id: String,
    onEscFormInput: {
      default: () => {},
      required: false,
      type: Function
    },
    placeholder: String,
    source: Function,
    value: Object,
  },
  data() {
    return {
      isOpen: false,
      isLoading: false,
      limit: 20,
      query: null,
      onTextInput: this.debounce(this._onTextInput, 200),
      suggestions: [],
      suggestionElements: [],
      suggestionFocusIndex: null,
    };
  },
  watch: {
    disabled(isDisabled) {
      if (isDisabled) {
        this.closeSuggestions();
      }
    }
  },
  mounted() {
    document.addEventListener('click', this.onClickOutside)
  },
  destroyed() {
    document.removeEventListener('click', this.onClickOutside)
  },
  methods: {
    closeSuggestions() {
      this.isOpen = false;
      this.$nextTick(() => {
        if (!this.value) {
          this.query = null;
        }
      });
    },
    highlightQuery(string) {
      var regex = new RegExp(this.query, 'i');
      var match = string.match(regex);
      if (!match) {
        return string;
      }
      var matchedText = string.substring(match.index, match.index + match[0].toString().length);
      return string.replace(regex, `<strong>${matchedText}</strong>`);
    },
    onArrowDown() {
      if (this.suggestionElements.length) {
        if (this.suggestionFocusIndex === null) {
          this.suggestionFocusIndex = 0;
          this.suggestionElements[this.suggestionFocusIndex].focus();
        } else if (this.suggestionFocusIndex + 1 < this.suggestionElements.length) {
          this.suggestionFocusIndex++;
          this.suggestionElements[this.suggestionFocusIndex].focus();
        }
      }
    },
    onArrowUp() {
      if (this.suggestionElements.length) {
        if (this.suggestionFocusIndex === 0) {
          this.suggestionFocusIndex = null;
          this.$refs.autocompleteInput.$el.focus();
        } else if (this.suggestionFocusIndex) {
          this.suggestionFocusIndex--;
          this.suggestionElements[this.suggestionFocusIndex].focus();
        }
      }
    },
    onClickOutside(evt) {
      if (!this.$el.contains(evt.target)) {
        this.closeSuggestions();
      }
    },
    onEsc() {
      this.closeSuggestions();
    },
    _onTextInput() {
      this.$emit('input', null);
      if (this.query.length > 1) {
        this.isOpen = true;
        this.isLoading = true;
        this.suggestions = [];
        this.source(this.query.replace(/[^\w ]+/g, ''), this.limit).then(results => {
          this.populateSuggestions(results);
        });
      } else {
        this.isOpen = false;
      }
    },
    populateSuggestions(results) {
      this.suggestions = results;
      this.isLoading = false;
      this.isOpen = true;
      this.suggestionFocusIndex = null;
      this.$nextTick(() => {
        this.suggestionElements = this.$refs.autocompleteSuggestions.querySelectorAll('.dropdown-item');
      });
    },
    selectSuggestion(suggestion) {
      this.isOpen = false;
      this.query = suggestion.label;
      this.$emit('input', suggestion);
    }
  }
};
</script>

<style scoped>
.autocomplete-dropdown-menu {
  position: static;
}
.dropdown {
  z-index: 100;
}
.dropdown-menu-open {
  display: block;
}
</style>
