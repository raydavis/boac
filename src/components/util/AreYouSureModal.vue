<template>
  <b-modal
    id="are-you-sure-modal"
    v-model="showAreYouSureModal"
    :no-close-on-backdrop="true"
    @cancel.prevent="functionCancel"
    @hide.prevent="functionCancel"
    @shown="putFocusNextTick('are-you-sure-confirm')"
    body-class="pl-0 pr-0"
    hide-footer
    hide-header>
    <div>
      <div class="modal-header">
        <h3 id="are-you-sure-header">{{ modalHeader }}</h3>
      </div>
      <div id="are-you-sure-body" v-if="modalBody" class="modal-body">
        <span v-html="modalBody"></span>
      </div>
      <div class="modal-footer">
        <form @submit.prevent="functionConfirm">
          <b-btn
            id="are-you-sure-confirm"
            :aria-label="modalHeader"
            @click.prevent="functionConfirm"
            class="btn-primary-color-override"
            variant="primary">
            {{ buttonLabelConfirm }}
          </b-btn>
          <b-btn
            id="are-you-sure-cancel"
            @click.stop="functionCancel"
            class="pl-2"
            variant="link">
            {{ buttonLabelCancel }}
          </b-btn>
        </form>
      </div>
    </div>
  </b-modal>
</template>

<script>
import Util from '@/mixins/Util';

export default {
  name: 'AreYouSureModal',
  mixins: [Util],
  props: {
    buttonLabelCancel: {
      type: String,
      required: false,
      default: 'Cancel'
    },
    buttonLabelConfirm: {
      type: String,
      required: false,
      default: 'Confirm'
    },
    functionCancel: {
      type: Function,
      required: true
    },
    functionConfirm: {
      type: Function,
      required: true
    },
    modalBody: {
      type: String,
      required: false,
      default: null
    },
    modalHeader: {
      type: String,
      required: false,
      default: 'Are you sure?'
    },
    showModal: {
      type: Boolean,
      required: true
    }
  },
  data: () => ({
    showAreYouSureModal: false
  }),
  watch: {
    showModal(value) {
      this.showAreYouSureModal = value;
    }
  },
  created() {
    this.showAreYouSureModal = this.showModal;
  }
}
</script>
