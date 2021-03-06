<template>
  <div>
    <div
      v-if="totalCourseCount"
      tabindex="0">
      <h1
        id="course-results-page-h1"
        v-if="renderPrimaryHeader"
        class="page-section-header">
        {{ 'class' | pluralize(totalCourseCount, {1: '1'}, 'es') }} matching '{{ searchPhrase }}'
      </h1>
      <h2
        id="course-results-page-h2"
        v-if="!renderPrimaryHeader"
        class="page-section-header">
        {{ 'class' | pluralize(totalCourseCount, {1: '1'}, 'es') }} matching '{{ searchPhrase }}'
      </h2>
      <div v-if="courses.length < totalCourseCount">
        Showing the first {{ courses.length }} classes.
      </div>
    </div>
    <table v-if="totalCourseCount" class="table-full-width">
      <tr>
        <th>
          <button
            id="column-sort-button-section"
            :aria-label="`Sort by section ${describeReverse(sort.reverse.section)}`"
            @click="courseSort('section')"
            @keyup.enter="courseSort('section')"
            class="btn btn-link table-header-text sortable-table-header cursor-pointer table-cell"
            tabindex="0">
            Section
            <span v-if="sort.by === 'section'">
              <font-awesome :icon="sort.reverse.section ? 'caret-down' : 'caret-up'" />
            </span>
          </button>
        </th>
        <th>
          <button
            id="column-sort-button-title"
            :aria-label="`Sort by course name ${describeReverse(sort.reverse.title)}`"
            @click="courseSort('title')"
            @keyup.enter="courseSort('title')"
            class="btn btn-link table-header-text sortable-table-header cursor-pointer table-cell"
            tabindex="0">
            Course Name
            <span v-if="sort.by === 'title'">
              <font-awesome :icon="sort.reverse.title ? 'caret-down' : 'caret-up'" />
            </span>
          </button>
        </th>
        <th class="sortable-table-header table-cell">
          <span class="table-header-text">Instructor(s)</span>
        </th>
      </tr>
      <tr v-for="course in sortedCourses" :key="course.id">
        <td class="table-cell">
          <span class="sr-only">Section</span>
          <router-link :to="`/course/${course.termId}/${course.sectionId}`">
            {{ course.courseName }} - {{ course.instructionFormat }} {{ course.sectionNum }}
          </router-link>
        </td>
        <td class="table-cell">
          <span class="sr-only">Course Name</span>
          {{ course.courseTitle }}
        </td>
        <td class="table-cell">{{ course.instructors }}</td>
      </tr>
    </table>
  </div>
</template>

<script>
import Context from '@/mixins/Context';
import UserMetadata from '@/mixins/UserMetadata';

export default {
  name: 'SortableCourseList',
  mixins: [Context, UserMetadata],
  props: {
    searchPhrase: String,
    courses: Array,
    totalCourseCount: Number,
    renderPrimaryHeader: Boolean
  },
  data: () => ({
    sort: {
      by: null,
      reverse: {
        section: false,
        title: false
      }
    },
    sortedCourses: []
  }),
  created() {
    this.sort.by = 'section';
    this.sortedCourses = this.courses.sort(this.courseComparator);
  },
  methods: {
    courseSort(sortBy) {
      if (this.sort.by !== sortBy) {
        this.sort.by = sortBy;
        this.sort.reverse[sortBy] = false;
        this.sortedCourses = this.courses.sort(this.courseComparator);
      } else {
        this.sort.reverse[sortBy] = !this.sort.reverse[sortBy];
        this.sortedCourses = this.sortedCourses.reverse();
      }
      this.alertScreenReader(`Courses sorted by ${this.sort.by === 'section' ? 'section' : 'course name'} ${this.describeReverse(this.sort.reverse[this.sort.by])}`);
    },
    courseComparator(c1, c2) {
      if (this.sort.by === 'title' && c1.courseTitle !== c2.courseTitle) {
        return c1.courseTitle > c2.courseTitle ? 1 : -1;
      }
      // If sorting by section name, attempt to compare by subject area.
      let split1 = this.splitCourseName(c1);
      let split2 = this.splitCourseName(c2);
      if (split1[0] > split2[0]) {
        return 1;
      }
      if (split1[0] < split2[0]) {
        return -1;
      }
      // If subject areas are identical, extract and compare numeric portion of catalog id.
      let code1 = parseInt(split1[1].match(/\d+/)[0], 10);
      let code2 = parseInt(split2[1].match(/\d+/)[0], 10);
      if (code1 > code2) {
        return 1;
      }
      if (code1 < code2) {
        return -1;
      }
      // If catalog ids are numerically identical then handle prefixes and suffixes with alphabetic comparison.
      if (split1[1] > split2[1]) {
        return 1;
      }
      if (split1[1] < split2[1]) {
        return -1;
      }
      // Instruction format and section number.
      if (c1.instructionFormat > c2.instructionFormat) {
        return 1;
      }
      if (c1.instructionFormat < c2.instructionFormat) {
        return -1;
      }
      return c1.sectionNum > c2.sectionNum ? 1 : -1;
    },
    splitCourseName(course) {
      let split = course.courseName.split(' ');
      return [split.slice(0, -1).join(' '), split[split.length - 1]];
    },
    describeReverse: reverse => (reverse ? 'descending' : '')
  }
};
</script>

<style scoped>
.table-cell {
  padding: 5px 10px 5px 0;
  vertical-align: top;
  width: 33%;
}
.table-header-text {
  color: #999 !important;
  font-size: 12px;
  font-weight: bold;
  padding: 0;
  text-decoration: none;
  width: fit-content;
}
.table-header-text:focus {
  outline: -webkit-focus-ring-color auto 5px;
}
</style>
