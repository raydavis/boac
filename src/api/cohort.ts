import axios from 'axios';
import store from '@/store';

export function getCohort(id: number, includeStudents = true) {
  let apiBaseUrl = store.getters['context/apiBaseUrl'];
  return axios
    .get(`${apiBaseUrl}/api/cohort/${id}?includeStudents=${includeStudents}`)
    .then(response => response.data, () => null);
}

export function getCohortPerFilters(filters: any[]) {
  let apiBaseUrl = store.getters['context/apiBaseUrl'];
  return axios
    .post(`${apiBaseUrl}/api/cohort/per_filters`, {
      filters: filters
    })
    .then(response => response.data, () => null);
}

export function getMyCohorts() {
  let apiBaseUrl = store.getters['context/apiBaseUrl'];
  return axios
    .get(`${apiBaseUrl}/api/cohorts/my`)
    .then(response => response.data, () => null);
}

export function getUsersWithCohorts() {
  let apiBaseUrl = store.getters['context/apiBaseUrl'];
  return axios
    .get(`${apiBaseUrl}/api/cohorts/all`)
    .then(response => response.data, () => null);
}

export function deleteCohort(id) {
  let apiBaseUrl = store.getters['context/apiBaseUrl'];
  return axios
    .delete(`${apiBaseUrl}/api/cohort/delete/${id}`, {
      headers: {
        'Content-Type': 'application/json'
      }
    })
    .then(() => store.commit('cohort/deleteCohort', id), () => null);
}

export function saveCohort(
  id: number,
  name: string,
  filterCriteria?: any,
  studentCount?: number
) {
  let apiBaseUrl = store.getters['context/apiBaseUrl'];
  return axios
    .post(`${apiBaseUrl}/api/cohort/update`, {
      id,
      name,
      filterCriteria,
      studentCount
    })
    .then(response => response.data, () => null);
}
