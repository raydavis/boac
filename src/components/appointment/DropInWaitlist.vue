<template>
  <div>
    <CreateAppointmentModal
      v-if="showCreateAppointmentModal"
      :cancel="cancelCreateAppointment"
      :create-appointment="createAppointment"
      :show-modal="showCreateAppointmentModal" />
    <div v-if="isHomepage">
      <div class="align-items-center d-flex homepage-header-border justify-content-between">
        <div>
          <h2 class="page-section-header">Drop-in Waitlist - {{ $moment() | moment('MMM D') }}</h2>
        </div>
        <div>
          <b-btn
            id="create-drop-in-appointment"
            variant="link"
            class="mb-1"
            aria-label="Create new drop-in appointment"
            @click="showCreateAppointmentModal = true">
            <font-awesome icon="plus" />
          </b-btn>
        </div>
      </div>
    </div>
    <div v-if="!isHomepage">
      <div class="mb-4 mt-4 text-center">
        <b-btn
          id="new-drop-in-appointment"
          variant="primary"
          class="btn-primary-color-override pl-3 pr-3"
          aria-label="Create new drop-in appointment"
          @click="showCreateAppointmentModal = true">
          New Drop-in Appointment
        </b-btn>
      </div>
      <div class="border-bottom d-flex justify-content-between">
        <div>
          <h1 class="font-size-18 font-weight-bold text-nowrap">Today's Drop-In Waitlist ({{ size(waitlist) }})</h1>
        </div>
        <div>
          <h2 class="font-size-18 font-weight-bold text-nowrap">{{ $moment() | moment('ddd, MMM D') }}</h2>
        </div>
      </div>
    </div>
    <div v-if="isEmpty(waitlist)" class="border-bottom">
      <div class="font-size-16 mb-3 ml-1 mt-3">
        No appointments yet
      </div>
    </div>
    <div v-if="!isEmpty(waitlist)">
      <div
        v-for="(appointment, index) in waitlist"
        :key="appointment.id"
        class="align-items-start border-bottom d-flex font-size-16 justify-content-between mb-3 ml-1 mt-3">
        <div class="mr-3 text-nowrap">
          <span class="sr-only">Created at </span>{{ new Date(appointment.createdAt) | moment('LT') }}
        </div>
        <div>
          <div class="d-flex">
            <div v-if="isHomepage" class="mr-2">
              <StudentAvatar size="small" :student="appointment.student" />
            </div>
            <div>
              <router-link
                v-if="linkToStudentProfiles"
                :id="`link-to-student-${appointment.student.uid}`"
                :to="studentRoutePath(appointment.student.uid, user.inDemoMode)">
                <span :id="`waitlist-student-name-${index}`">{{ appointment.student.name }}</span>
              </router-link>
              <div v-if="!linkToStudentProfiles">
                <span :id="`waitlist-student-name-${index}`">{{ appointment.student.name }}</span>
              </div>
              <div class="font-size-12">
                {{ oxfordJoin(appointment.topics) }}
              </div>
            </div>
          </div>
        </div>
        <div class="flex-grow-1">
          <div class="float-right">
            <b-dropdown
              class="bg-white mb-3"
              split
              :disabled="!!appointment.checkedInBy || !!appointment.canceledAt"
              text="Check In"
              variant="outline-dark"
              @click="launchCheckInForAppointment(appointment)">
              <b-dropdown-item-button @click="showAppointmentDetails(appointment)">Details</b-dropdown-item-button>
              <b-dropdown-item-button @click="cancelAppointment(appointment)">Cancel</b-dropdown-item-button>
            </b-dropdown>
            <AppointmentDetailsModal
              v-if="showAppointmentDetailsModal"
              :appointment="selectedAppointment"
              :close="closeAppointmentDetailsModal"
              :check-in="launchCheckIn"
              :show-modal="showAppointmentDetailsModal"
              :student="selectedAppointment.student" />
            <AppointmentCancellationModal
              v-if="showCancelAppointmentModal"
              :appointment="selectedAppointment"
              :appointment-cancellation="appointmentCancellation"
              :close="closeAppointmentCancellationModal"
              :show-modal="showCancelAppointmentModal"
              :student="selectedAppointment.student" />
            <CheckInModal
              v-if="showCheckInModal"
              :appointment="selectedAppointment"
              :appointment-checkin="checkInAppointment"
              :close="closeCheckInModal"
              :show-modal="showCheckInModal" />
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import AppointmentDetailsModal from '@/components/appointment/AppointmentDetailsModal';
import AppointmentCancellationModal from '@/components/appointment/AppointmentCancellationModal';
import CheckInModal from '@/components/appointment/CheckInModal';
import CreateAppointmentModal from '@/components/appointment/CreateAppointmentModal';
import StudentAvatar from '@/components/student/StudentAvatar';
import UserMetadata from '@/mixins/UserMetadata';
import Util from '@/mixins/Util';
import { cancel as apiCancel, checkIn as apiCheckIn, create as apiCreate } from '@/api/appointments';

export default {
  name: 'DropInWaitlist',
  components: {AppointmentCancellationModal, AppointmentDetailsModal, CheckInModal, CreateAppointmentModal, StudentAvatar},
  mixins: [UserMetadata, Util],
  props: {
    deptCode: {
      type: String,
      required: true
    },
    isHomepage: {
      type: Boolean,
      default: false
    },
    waitlist: {
      type: Array,
      required: true
    }
  },
  data: () => ({
    linkToStudentProfiles: undefined,
    now: undefined,
    selectedAppointment: undefined,
    showAppointmentDetailsModal: false,
    showCancelAppointmentModal: false,
    showCheckInModal: false,
    showCreateAppointmentModal: false
  }),
  created() {
    this.linkToStudentProfiles = this.user.isAdmin || this.dropInAdvisorDeptCodes().length;
    this.now = this.$moment();
  },
  methods: {
    appointmentCancellation(appointmentId, reason, reasonExplained) {
      apiCancel(this.selectedAppointment.id, reason, reasonExplained).then(canceled => {
        const indexOf = this.waitlist.findIndex(a => a.id === canceled.id);
        this.waitlist.splice(indexOf, 1);
      });
    },
    cancelAppointment(appointment) {
      this.selectedAppointment = appointment;
      this.showCancelAppointmentModal = true;
    },
    cancelCreateAppointment() {
      this.showCreateAppointmentModal = false;
      this.selectedAppointment = undefined;
    },
    checkInAppointment(advisor, deptCodes) {
      if (!advisor) {
        advisor = this.user;
        deptCodes = this.map(this.user.departments, 'code');
      }
      const appointmentId = this.selectedAppointment.id;
      apiCheckIn(
        deptCodes,
        advisor.name,
        advisor.title,
        advisor.uid,
        appointmentId
      ).then(() => {
        const index = this.findIndex(this.waitlist, {'id': appointmentId});
        if (index !== -1) {
          this.waitlist.splice(index, 1);
        }
      });
    },
    closeAppointmentCancellationModal() {
      this.showCancelAppointmentModal = false;
      this.selectedAppointment = undefined;
    },
    closeAppointmentDetailsModal() {
      this.showAppointmentDetailsModal = false;
      this.selectedAppointment = undefined;
    },
    closeCheckInModal() {
      this.showCheckInModal = false;
      this.showAppointmentDetailsModal = false;
      this.selectedAppointment = undefined;
    },
    createAppointment(details, sid, topics) {
      apiCreate(this.deptCode, details, sid, 'Drop-in', topics).then(appointment => {
        this.showCreateAppointmentModal = false;
        this.waitlist.push(appointment);
      });
    },
    launchCheckIn() {
      if (this.isHomepage) {
        this.checkInAppointment();
      } else {
        this.showCheckInModal = true;
      }
    },
    launchCheckInForAppointment(appointment) {
      this.selectedAppointment = appointment;
      this.launchCheckIn();
    },
    showAppointmentDetails(appointment) {
      this.selectedAppointment = appointment;
      this.showAppointmentDetailsModal = true;
    }
  }
}
</script>