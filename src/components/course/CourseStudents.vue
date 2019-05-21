<template>
  <b-table
    :borderless="true"
    :fields="fields"
    :items="section.students"
    :small="true"
    stacked="md"
    :tbody-tr-class="rowClass"
    thead-class="sortable-table-header">
    <template slot="curated" slot-scope="row">
      <div>
        <CuratedStudentCheckbox :student="row.item" class="curated-checkbox" />
      </div>
    </template>

    <template slot="avatar" slot-scope="row">
      <StudentAvatar :key="row.item.sid" :student="row.item" size="medium" />
    </template>

    <template slot="profile" slot-scope="row">
      <div>
        <router-link :id="row.item.uid" :to="`/student/${row.item.uid}`">
          <h3
            class="student-name m-0 p-0"
            :class="{'demo-mode-blur': user.inDemoMode}">
            {{ row.item.lastName }}<span v-if="row.item.firstName">, {{ row.item.firstName }}</span>
          </h3>
        </router-link>
      </div>
      <div :id="`row-${row.index}-student-sid`" class="student-sid" :class="{'demo-mode-blur': user.inDemoMode}">
        {{ row.item.sid }}
        <span v-if="row.item.enrollment.enrollmentStatus === 'W'" class="red-flag-status">WAITLISTED</span>
        <span v-if="displayAsInactive(row.item)" class="red-flag-status">INACTIVE</span>
      </div>
      <div>
        <span class="student-text">{{ row.item.level }}</span>
      </div>
      <div>
        <div v-for="major in row.item.majors" :key="major" class="student-text">{{ major }}</div>
      </div>
      <div>
        <div v-if="row.item.athleticsProfile" class="student-teams-container">
          <div v-for="membership in row.item.athleticsProfile.athletics" :key="membership.groupName" class="student-teams">
            {{ membership.groupName }}
          </div>
        </div>
      </div>
    </template>

    <template slot="courseSites" slot-scope="row">
      <div class="course-sites font-size-14 pl-2">
        <div
          v-for="canvasSite in row.item.enrollment.canvasSites"
          :key="canvasSite.courseCode">
          <strong>{{ canvasSite.courseCode }}</strong>
        </div>
        <div v-if="!row.item.enrollment.canvasSites.length">
          No course site
        </div>
      </div>
    </template>

    <template slot="assignmentsSubmitted" slot-scope="row">
      <div v-if="row.item.enrollment.canvasSites.length">
        <div
          v-for="canvasSite in row.item.enrollment.canvasSites"
          :key="canvasSite.canvasCourseId">
          <span v-if="row.item.enrollment.canvasSites.length > 1" class="sr-only">
            {{ canvasSite.courseCode }}
          </span>
          <div v-if="canvasSite.analytics.assignmentsSubmitted.courseDeciles" class="font-size-14 text-nowrap">
            <strong>{{ canvasSite.analytics.assignmentsSubmitted.student.raw }}</strong>
            <span class="faint-text">
              (Max: {{ canvasSite.analytics.assignmentsSubmitted.courseDeciles[10] }})
            </span>
          </div>
          <div v-if="!canvasSite.analytics.assignmentsSubmitted.courseDeciles" class="font-size-14">
            No Data
          </div>
        </div>
      </div>
      <span
        v-if="!row.item.enrollment.canvasSites.length"><span class="sr-only">No data</span>&mdash;</span>
    </template>

    <template slot="assignmentGrades" slot-scope="row">
      <div>
        <div
          v-for="canvasSite in row.item.enrollment.canvasSites"
          :key="canvasSite.canvasCourseId"
          class="profile-boxplot-container">
          <span v-if="row.item.enrollment.canvasSites.length > 1" class="sr-only">
            {{ canvasSite.courseCode }}
          </span>
          <StudentBoxplot
            v-if="canvasSite.analytics.currentScore.boxPlottable"
            :dataset="canvasSite.analytics"
            :numeric-id="row.item.uid + '-' + canvasSite.canvasCourseId.toString()"></StudentBoxplot>
          <div v-if="canvasSite.analytics.currentScore.boxPlottable" class="sr-only">
            <div>User score: {{ canvasSite.analytics.currentScore.student.raw }}</div>
            <div>Maximum:  {{ canvasSite.analytics.currentScore.courseDeciles[10] }}</div>
            <div>70th Percentile: {{ canvasSite.analytics.currentScore.courseDeciles[7] }}</div>
            <div>50th Percentile: {{ canvasSite.analytics.currentScore.courseDeciles[5] }}</div>
            <div>30th Percentile: {{ canvasSite.analytics.currentScore.courseDeciles[3] }}</div>
            <div>Minimum: {{ canvasSite.analytics.currentScore.courseDeciles[0] }}</div>
          </div>
          <div v-if="!canvasSite.analytics.currentScore.boxPlottable" class="font-size-14">
            <div v-if="canvasSite.analytics.currentScore.courseDeciles">
              Score: <strong>{{ canvasSite.analytics.currentScore.student.raw }}</strong>
              <div class="faint-text">
                (Max: {{ canvasSite.analytics.currentScore.courseDeciles[10] }})
              </div>
            </div>
            <div v-if="!canvasSite.analytics.currentScore.courseDeciles">
              No Data
            </div>
          </div>
        </div>
        <span v-if="!row.item.enrollment.canvasSites.length"><span class="sr-only">No data</span>&mdash;</span>
      </div>
    </template>

    <template slot="bCourses" slot-scope="row">
      <div class="font-size-14">
        <div
          v-for="canvasSite in row.item.enrollment.canvasSites"
          :key="canvasSite.canvasCourseId"
          class="profile-boxplot-container">
          <span v-if="row.item.enrollment.canvasSites.length > 1" class="sr-only">
            {{ canvasSite.courseCode }}
          </span>
          {{ lastActivityDays(canvasSite.analytics) }}
        </div>
        <span v-if="!row.item.enrollment.canvasSites.length"><span class="sr-only">No data</span>&mdash;</span>
      </div>
    </template>

    <template slot="midtermGrade" slot-scope="row">
      <span v-if="row.item.enrollment.midtermGrade" v-accessible-grade="row.item.enrollment.midtermGrade" class="font-weight-bold font-size-14"></span>
      <i
        v-if="isAlertGrade(row.item.enrollment.midtermGrade)"
        class="fas fa-exclamation-triangle boac-exclamation"></i>
      <span v-if="!row.item.enrollment.midtermGrade"><span class="sr-only">No data</span>&mdash;</span>
    </template>

    <template slot="finalGrade" slot-scope="row">
      <span v-if="row.item.enrollment.grade" v-accessible-grade="row.item.enrollment.grade" class="font-weight-bold font-size-14"></span>
      <i
        v-if="isAlertGrade(row.item.enrollment.grade)"
        class="fas fa-exclamation-triangle boac-exclamation"></i>
      <span v-if="!row.item.enrollment.grade" class="cohort-grading-basis">
        {{ row.item.enrollment.gradingBasis }}
      </span>
    </template>
  </b-table>
</template>

<script>
import CuratedStudentCheckbox from '@/components/curated/CuratedStudentCheckbox';
import StudentAnalytics from '@/mixins/StudentAnalytics';
import StudentAvatar from '@/components/student/StudentAvatar';
import StudentBoxplot from '@/components/student/StudentBoxplot';
import StudentMetadata from '@/mixins/StudentMetadata';
import UserMetadata from '@/mixins/UserMetadata';

export default {
  name: "CourseStudents",
  components: {
    CuratedStudentCheckbox,
    StudentAvatar,
    StudentBoxplot
  },
  mixins: [
    StudentAnalytics,
    StudentMetadata,
    UserMetadata
  ],
  props: {
    featured: String,
    section: Object
  },
  data: () => ({
    fields: [
      {key: 'curated', label: '', class: 'pl-3'},
      {key: 'avatar', label: ''},
      {key: 'profile', label: ''},
      {key: 'courseSites', label: 'Course Site(s)'},
      {key: 'assignmentsSubmitted', label: 'Assignments Submitted'},
      {key: 'assignmentGrades', label: 'Assignment Grades'},
      {key: 'bCourses', label: 'bCourses Activity'},
      {key: 'midtermGrade', label: 'Mid'},
      {key: 'finalGrade', label: 'Final', class: 'pr-3'}
    ]
  }),
  methods: {
    rowClass(item) {
      return this.featured === item.uid ? 'list-group-item-info row-border pb-2 pt-2' : 'row-border pb-2 pt-2';
    }
  }
}
</script>

<style scoped>
.course-sites {
  border-left: 1px solid #ddd;
}
.curated-checkbox {
  padding-top: 36px;
}
.course-list-view-column-profile button {
  padding: 2px 0 0 5px;
}
.student-name {
  color: #49b;
  font-size: 16px;
  max-width: 150px;
}
</style>