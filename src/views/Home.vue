<template>
  <div class="ml-3 mt-3">
    <h1 class="sr-only">Welcome to BOA</h1>
    <Spinner alert-prefix="The BOA homepage" />
    <div v-if="!loading" class="home-content">
      <div>
        <div id="filtered-cohorts-header-row">
          <h2 id="no-cohorts-header" v-if="myCohorts && !size(myCohorts)" class="page-section-header">
            You have no saved cohorts.
          </h2>
          <h1 v-if="myCohorts && size(myCohorts)" class="page-section-header">
            Cohorts
          </h1>
        </div>
        <div v-if="myCohorts && !size(myCohorts)">
          <router-link id="create-filtered-cohort" to="/cohort/new">Create a student cohort</router-link>
          automatically by your filtering preferences, such as GPA or units.
        </div>
        <div role="tablist" class="panel-group">
          <SortableGroup
            v-for="cohort in myCohorts"
            :key="cohort.id"
            :group="cohort"
            :is-cohort="true" />
        </div>
      </div>
      <div v-if="size(myCuratedGroups)">
        <div id="curated-groups-header-row">
          <h2 class="page-section-header">Curated Groups</h2>
        </div>
        <SortableGroup
          v-for="curatedGroup in myCuratedGroups"
          :key="curatedGroup.id"
          :group="curatedGroup"
          :is-cohort="false" />
      </div>
    </div>
  </div>
</template>

<script>
import Loading from '@/mixins/Loading.vue';
import Scrollable from '@/mixins/Scrollable';
import SortableGroup from '@/components/search/SortableGroup.vue';
import Spinner from '@/components/util/Spinner.vue';
import UserMetadata from '@/mixins/UserMetadata.vue';
import Util from '@/mixins/Util.vue';

export default {
  name: 'Home',
  components: {
    SortableGroup,
    Spinner
  },
  mixins: [Loading, Scrollable, UserMetadata, Util],
  watch: {
    myCohorts: function() {
      if (this.myCohorts) {
        this.loaded('Home');
      }
    },
    myCuratedGroups: function() {
      if (this.myCuratedGroups) {
        this.loaded('Home');
      }
    }
  },
  mounted() {
    if (this.myCohorts || this.myCuratedGroups) {
      this.loaded('Home');
      this.scrollToTop();
    }
  }
};
</script>

<style scoped>
.home-content {
  display: flex;
  flex-direction: column;
}
</style>
