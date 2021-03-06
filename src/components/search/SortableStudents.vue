<template>
  <div>
    <b-table
      :borderless="true"
      :fields="fields"
      :items="students"
      :no-sort-reset="true"
      :small="true"
      :sort-by.sync="sortBy"
      :sort-compare="sortCompare"
      :sort-desc.sync="sortDescending"
      stacked="md"
      thead-class="sortable-table-header text-nowrap">
      <template v-slot:cell(curated)="row">
        <CuratedStudentCheckbox v-if="options.includeCuratedCheckbox" :student="row.item" />
      </template>

      <template v-slot:cell(avatar)="row">
        <StudentAvatar :key="row.item.sid" :student="row.item" size="small" />
      </template>

      <template v-slot:cell(lastName)="row">
        <span class="sr-only">Student name</span>
        <router-link
          :id="`link-to-student-${row.item.uid}`"
          :aria-label="`Go to profile page of ${row.item.name}`"
          :class="{'demo-mode-blur': user.inDemoMode}"
          :to="studentRoutePath(row.item.uid, user.inDemoMode)"
          v-html="`${row.item.lastName}, ${row.item.firstName}`"></router-link>
        <span
          v-if="row.item.academicCareerStatus === 'Inactive' || displayAsAscInactive(row.item) || displayAsCoeInactive(row.item)"
          class="inactive-info-icon sortable-students-icon"
          uib-tooltip="Inactive"
          tooltip-placement="bottom">
          <font-awesome icon="info-circle" />
        </span>
        <span
          v-if="row.item.academicCareerStatus === 'Completed'"
          class="sortable-students-icon"
          uib-tooltip="Graduated"
          tooltip-placement="bottom">
          <font-awesome icon="graduation-cap" />
        </span>
      </template>

      <template v-slot:cell(sid)="row">
        <span class="sr-only">S I D</span>
        <span :class="{'demo-mode-blur': user.inDemoMode}">{{ row.item.sid }}</span>
      </template>

      <template v-slot:cell(majors[0])="row" v-if="!options.compact">
        <span class="sr-only">Major</span>
        <div v-if="!row.item.majors || row.item.majors.length === 0">--<span class="sr-only">No data</span></div>
        <div
          v-for="major in row.item.majors"
          :key="major">
          {{ major }}
        </div>
      </template>

      <template v-slot:cell(expectedGraduationTerm.id)="row" v-if="!options.compact">
        <span class="sr-only">Expected graduation term</span>
        <div v-if="!row.item.expectedGraduationTerm">--<span class="sr-only">No data</span></div>
        <span class="text-nowrap">{{ abbreviateTermName(row.item.expectedGraduationTerm && row.item.expectedGraduationTerm.name) }}</span>
      </template>

      <template v-slot:cell(term.enrolledUnits)="row" v-if="!options.compact">
        <span class="sr-only">Term units</span>
        <div>{{ get(row.item.term, 'enrolledUnits', 0) }}</div>
      </template>

      <template v-slot:cell(cumulativeUnits)="row" v-if="!options.compact">
        <span class="sr-only">Units completed</span>
        <div v-if="!row.item.cumulativeUnits">--<span class="sr-only">No data</span></div>
        <div v-if="row.item.cumulativeUnits">{{ row.item.cumulativeUnits | numFormat('0.00') }}</div>
      </template>

      <template v-slot:cell(cumulativeGPA)="row" v-if="!options.compact">
        <span class="sr-only">GPA</span>
        <div v-if="isNil(row.item.cumulativeGPA)">--<span class="sr-only">No data</span></div>
        <div v-if="!isNil(row.item.cumulativeGPA)">{{ row.item.cumulativeGPA | round(3) }}</div>
      </template>

      <template v-slot:cell(alertCount)="row">
        <span class="sr-only">Issue count</span>
        <div class="float-right mr-2">
          <div
            v-if="!row.item.alertCount"
            :aria-label="`No alerts for ${row.item.name}`"
            class="bg-white border pl-3 pr-3 rounded-pill text-muted"
            tabindex="0">
            0
          </div>
          <div
            v-if="row.item.alertCount"
            :aria-label="`${row.item.alertCount} alerts for ${row.item.name}`"
            class="bg-white border border-warning font-weight-bolder pill-alerts-per-student pl-3 pr-3 rounded-pill"
            tabindex="0">
            {{ row.item.alertCount }}
          </div>
        </div>
      </template>
    </b-table>
  </div>
</template>

<script>
import Context from '@/mixins/Context';
import CuratedStudentCheckbox from '@/components/curated/CuratedStudentCheckbox';
import StudentAvatar from '@/components/student/StudentAvatar';
import StudentMetadata from '@/mixins/StudentMetadata';
import UserMetadata from '@/mixins/UserMetadata';
import Util from '@/mixins/Util';

export default {
  name: 'SortableStudents',
  components: {
    CuratedStudentCheckbox,
    StudentAvatar
  },
  mixins: [Context, StudentMetadata, UserMetadata, Util],
  props: {
    options: {
      type: Object,
      default: () => ({
        compact: false,
        includeCuratedCheckbox: false,
        reverse: false,
        sortBy: 'lastName'
      })
    },
    students: {
      required: true,
      type: Array
    }
  },
  data() {
    return {
      fields: undefined,
      sortBy: this.options.sortBy,
      sortDescending: this.options.reverse
    }
  },
  watch: {
    sortBy() {
      this.onChangeSortBy();
    },
    sortDescending() {
      this.onChangeSortBy();
    }
  },
  created() {
    this.fields = [
      {key: 'curated', label: ''},
      {key: 'avatar', label: '', class: 'pr-0'},
      {key: 'lastName', label: 'Name', sortable: true},
      {key: 'sid', label: 'SID', sortable: true}
    ];
    if (this.options.compact) {
      this.fields = this.fields.concat([
        {key: 'alertCount', label: 'Alerts', sortable: true, class: 'alert-count text-right'}
      ]);
    } else {
      this.fields = this.fields.concat([
        {key: 'majors[0]', label: 'Major', sortable: true, class: 'truncate-with-ellipsis'},
        {key: 'expectedGraduationTerm.id', label: 'Grad', sortable: true},
        {key: 'term.enrolledUnits', label: 'Term units', sortable: true},
        {key: 'cumulativeUnits', label: 'Units completed', sortable: true},
        {key: 'cumulativeGPA', label: 'GPA', sortable: true},
        {key: 'alertCount', label: 'Alerts', sortable: true, class: 'alert-count text-right'}
      ]);
    }
  },
  methods: {
    abbreviateTermName: termName =>
      termName &&
      termName
        .replace('20', " '")
        .replace('Spring', 'Spr')
        .replace('Summer', 'Sum'),
    normalizeForSort(value) {
      return this.isString(value) ? value.toLowerCase() : value;
    },
    onChangeSortBy() {
      const field = this.find(this.fields, ['key', this.sortBy]);
      this.alertScreenReader(`Sorted by ${field.label}${this.sortDescending ? ', descending' : ''}`);
    },
    sortCompare(a, b, sortBy, sortDesc) {
      let aValue = this.get(a, sortBy);
      let bValue = this.get(b, sortBy);
      // If column type is number then nil is treated as zero.
      aValue = this.isNil(aValue) && this.isNumber(bValue) ? 0 : this.normalizeForSort(aValue);
      bValue = this.isNil(bValue) && this.isNumber(aValue) ? 0 : this.normalizeForSort(bValue);
      let result = this.sortComparator(aValue, bValue);
      if (result === 0) {
        this.each(['lastName', 'firstName', 'sid'], field => {
          result = this.sortComparator(
            this.normalizeForSort(this.get(a, field)),
            this.normalizeForSort(this.get(b, field))
          );
          // Secondary sort is always ascending
          result *= sortDesc ? -1 : 1;
          // Break from loop if comparator result is non-zero
          return result === 0;
        });
      }
      return result;
    }
   }
};
</script>

<style>
th.alert-count {
  padding-right: 15px;
}
.sortable-students-icon {
  margin-left: 5px;
}
</style>
