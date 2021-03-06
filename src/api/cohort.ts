import axios from 'axios';
import moment from 'moment-timezone';
import store from '@/store';
import utils from '@/api/api-utils';

export function createCohort(
  name: string,
  filters: any[]
) {
  return axios
    .post(`${utils.apiBaseUrl()}/api/cohort/create`, {name, filters})
    .then(response => {
      const cohort = response.data;
      store.dispatch('cohort/addCohort', cohort);
      return cohort;
    }, () => null);
}

export function deleteCohort(id) {
  return axios
    .delete(`${utils.apiBaseUrl()}/api/cohort/delete/${id}`, {
      headers: {
        'Content-Type': 'application/json'
      }
    })
    .then(() => {
      store.commit('cohort/deleteCohort', id);
    }, () => null);
}

export function downloadCsv(cohortName: string, filters: any[], csvColumnsSelected: any[]) {
  const fileDownload = require('js-file-download');
  const now = moment().format('YYYY-MM-DD_HH-mm-ss');
  const filename = cohortName ? `${cohortName}-students-${now}` : `students-${now}`;
  return axios
    .post(`${utils.apiBaseUrl()}/api/cohort/download_csv_per_filters`, { filters, csvColumnsSelected })
    .then(response => fileDownload(response.data, `${filename}.csv`), () => null);
}

export function getCohort(
  id: number,
  includeStudents = true,
  orderBy = 'lastName'
) {
  return axios
    .get(
      `${utils.apiBaseUrl()}/api/cohort/${id}?includeStudents=${includeStudents}&orderBy=${orderBy}`
    )
    .then(response => response.data, () => null);
}

export function getCohortFilterOptions(owner: string, existingFilters: any[]) {
  owner = owner || 'me';
  return axios
    .post(`${utils.apiBaseUrl()}/api/cohort/filter_options/${owner}`, {
      existingFilters: existingFilters
    })
    .then(response => response.data, () => null);
}

export function getMyCohorts() {
  return axios
    .get(`${utils.apiBaseUrl()}/api/cohorts/my`)
    .then(response => response.data, () => null);
}

export function getStudentsPerFilters(
  filters: any[],
  orderBy: string,
  offset: number,
  limit: number
) {
  return axios
    .post(`${utils.apiBaseUrl()}/api/cohort/get_students_per_filters`, {
      filters,
      orderBy,
      offset,
      limit
    })
    .then(response => response.data, () => null);
}

export function getStudentsWithAlerts(cohortId) {
  return axios
    .get(`${utils.apiBaseUrl()}/api/cohort/${cohortId}/students_with_alerts`)
    .then(response => response.data, () => null);
}

export function getUsersWithCohorts() {
  return axios
    .get(`${utils.apiBaseUrl()}/api/cohorts/all`)
    .then(response => response.data, () => null);
}

export function saveCohort(
  id: number,
  name: string,
  filters?: any
) {
  return axios
    .post(`${utils.apiBaseUrl()}/api/cohort/update`, {
      id,
      name,
      filters
    })
    .then(response => {
      const cohort = response.data;
      store.dispatch('cohort/updateCohort', cohort);
      return cohort;
    }, () => null);
}

export function translateToFilterOptions(owner: string, criteria: any) {
  return axios
    .post(`${utils.apiBaseUrl()}/api/cohort/translate_to_filter_options/${owner}`, { criteria: criteria })
    .then(response => response.data, () => null);
}
