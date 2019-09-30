<template>
  <b-modal
    id="rename-note-template"
    v-model="showModalProxy"
    body-class="pl-0 pr-0"
    hide-footer
    hide-header-close
    title="Rename Your Template"
    @shown="focusModalById('rename-template-input')">
    <div>
      <form @submit.prevent="renameTemplate()">
        <div class="ml-3 mr-3">
          <label class="pb-2" for="rename-template-input">Template name:</label>
          <div>
            <input
              id="rename-template-input"
              v-model="title"
              class="cohort-create-input-name"
              type="text"
              maxlength="255"
              required>
          </div>
          <div class="faint-text mb-3"><span class="sr-only">Template name has a </span>255 character limit <span v-if="title.length">({{ 255 - title.length }} left)</span></div>
          <div
            v-if="error"
            id="rename-template-error"
            aria-live="polite"
            class="has-error">
            {{ error }}
          </div>
          <div
            v-if="title.length === 255"
            class="sr-only"
            aria-live="polite">
            Template name cannot exceed 255 characters.
          </div>
        </div>
        <div class="modal-footer pl-0 mr-2">
          <b-btn
            id="rename-template-confirm"
            class="btn-primary-color-override"
            variant="primary"
            :disabled="!title.length"
            @click.prevent="renameTemplate()">
            Rename
          </b-btn>
          <b-btn
            id="cancel-rename-template"
            variant="link"
            @click="cancelModal()">
            Cancel
          </b-btn>
        </div>
      </form>
    </div>
  </b-modal>
</template>

<script>
import Util from '@/mixins/Util';
import Validator from '@/mixins/Validator';

export default {
  name: 'RenameTemplateModal',
  mixins: [Util, Validator],
  props: {
    cancel: {
      type: Function,
      required: true
    },
    rename: {
      type: Function,
      required: true
    },
    showModal: {
      type: Boolean,
      required: true
    },
    template: {
      type: Object,
      required: true
    },
    toggleShow: {
      type: Function,
      required: true
    }
  },
  data: () => ({
    title: '',
    error: undefined
  }),
  computed: {
    showModalProxy: {
      get() {
        return this.showModal;
      },
      set(value) {
        this.toggleShow(value);
      }
    }
  },
  watch: {
    title() {
      this.error = undefined;
    }
  },
  mounted() {
    this.title = this.template.title;
  },
  methods: {
    cancelModal() {
      this.error = undefined;
      this.cancel();
    },
    renameTemplate: function() {
      this.error = this.validateTemplateTitle({ id: this.template.id, title: this.title });
      if (!this.error) {
        this.rename(this.title);
      }
    }
  }
}
</script>