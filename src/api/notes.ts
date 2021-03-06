import _ from 'lodash';
import axios from 'axios';
import store from '@/store';
import utils from '@/api/api-utils';
import Vue from 'vue';

export function getDistinctStudentCount(sids: string[], cohortIds: number[], curatedGroupIds: number[]) {
  return axios
    .post(`${utils.apiBaseUrl()}/api/notes/batch/distinct_student_count`, {sids, cohortIds, curatedGroupIds})
    .then(response => response.data, () => null);
}

export function getNote(noteId) {
  return axios
    .get(`${utils.apiBaseUrl()}/api/note/${noteId}`)
    .then(response => response.data, () => null);
}

export function markNoteRead(noteId) {
  return axios
    .post(`${utils.apiBaseUrl()}/api/notes/${noteId}/mark_read`)
    .then(response => {
      store.dispatch('user/gaNoteEvent', {
        id: noteId,
        name: `Advisor ${store.getters['user/uid']} read a note`,
        action: 'read'
      });
      return response.data
    }, () => null);
}

export function createNote(
    sid: any,
    subject: string,
    body: string,
    topics: string[],
    attachments: any[],
    templateAttachmentIds: []
) {
  const data = {sid, subject, body, topics, templateAttachmentIds};
  _.each(attachments || [], (attachment, index) => data[`attachment[${index}]`] = attachment);
  return utils.postMultipartFormData('/api/notes/create', data).then(data => {
    Vue.prototype.$eventHub.$emit('advising-note-created', data);
    store.dispatch('user/gaNoteEvent', {
      id: data.id,
      label: `Advisor ${store.getters['user/uid']} created a note`,
      action: 'create'
    });
    return data;
  });
}

export function createNoteBatch(
    sids: any,
    subject: string,
    body: string,
    topics: string[],
    attachments: any[],
    templateAttachmentIds: [],
    cohortIds: number[],
    curatedGroupIds: number[]
) {
  const data = {sids, subject, body, topics, templateAttachmentIds, cohortIds, curatedGroupIds};
  _.each(attachments || [], (attachment, index) => data[`attachment[${index}]`] = attachment);
  return utils.postMultipartFormData('/api/notes/batch/create', data).then(data => {
    Vue.prototype.$eventHub.$emit('batch-of-notes-created', data);
    store.dispatch('user/gaNoteEvent', {
      id: data.id,
      name: `Advisor ${store.getters['user/uid']} created a batch of notes`,
      action: 'batch_create'
    });
  });
}

export function updateNote(
    noteId: number,
    subject: string,
    body: string,
    topics: string[]
) {
  const data = {
    id: noteId,
    subject: subject,
    body: body,
    topics: topics
  };
  const api_json = utils.postMultipartFormData('/api/notes/update', data);
  store.dispatch('user/gaNoteEvent', {
    id: noteId,
    name: `Advisor ${store.getters['user/uid']} updated a note`,
    action: 'update'
  });
  return api_json;
}

export function deleteNote(noteId: number) {
  return axios
    .delete(`${utils.apiBaseUrl()}/api/notes/delete/${noteId}`)
    .then(response => response.data);
}

export function findAuthorsByName(query: string, limit: number) {
  let apiBaseUrl = store.getters['context/apiBaseUrl'];
  return axios
    .get(`${apiBaseUrl}/api/notes/authors/find_by_name?q=${query}&limit=${limit}`)
    .then(response => response.data);
}

export function addAttachment(noteId: number, attachment: any) {
  const data = {
    'attachment[0]': attachment,
  };
  return utils.postMultipartFormData(`/api/notes/${noteId}/attachment`, data);
}

export function removeAttachment(noteId: number, attachmentId: number) {
  return axios
    .delete(`${utils.apiBaseUrl()}/api/notes/${noteId}/attachment/${attachmentId}`)
    .then(response => response.data);
}
