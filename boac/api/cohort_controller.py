"""
Copyright ©2019. The Regents of the University of California (Regents). All Rights Reserved.

Permission to use, copy, modify, and distribute this software and its documentation
for educational, research, and not-for-profit purposes, without fee and without a
signed licensing agreement, is hereby granted, provided that the above copyright
notice, this paragraph and the following two paragraphs appear in all copies,
modifications, and distributions.

Contact The Office of Technology Licensing, UC Berkeley, 2150 Shattuck Avenue,
Suite 510, Berkeley, CA 94720-1620, (510) 643-7201, otl@berkeley.edu,
http://ipira.berkeley.edu/industry-info for commercial licensing opportunities.

IN NO EVENT SHALL REGENTS BE LIABLE TO ANY PARTY FOR DIRECT, INDIRECT, SPECIAL,
INCIDENTAL, OR CONSEQUENTIAL DAMAGES, INCLUDING LOST PROFITS, ARISING OUT OF
THE USE OF THIS SOFTWARE AND ITS DOCUMENTATION, EVEN IF REGENTS HAS BEEN ADVISED
OF THE POSSIBILITY OF SUCH DAMAGE.

REGENTS SPECIFICALLY DISCLAIMS ANY WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE. THE
SOFTWARE AND ACCOMPANYING DOCUMENTATION, IF ANY, PROVIDED HEREUNDER IS PROVIDED
"AS IS". REGENTS HAS NO OBLIGATION TO PROVIDE MAINTENANCE, SUPPORT, UPDATES,
ENHANCEMENTS, OR MODIFICATIONS.
"""

from datetime import datetime

from boac.api.errors import BadRequestError, ForbiddenRequestError, ResourceNotFoundError
from boac.api.util import advisor_required, is_unauthorized_search, response_with_students_csv_download
from boac.lib.berkeley import dept_codes_where_advising
from boac.lib.http import tolerant_jsonify
from boac.lib.util import get as get_param, get_benchmarker, to_bool_or_none as to_bool
from boac.merged import calnet
from boac.merged.cohort_filter_options import get_cohort_filter_options, translate_to_filter_options
from boac.merged.student import get_student_query_scope as get_query_scope, get_summary_student_profiles
from boac.models.authorized_user import AuthorizedUser
from boac.models.cohort_filter import CohortFilter
from flask import current_app as app, request
from flask_login import current_user


@app.route('/api/cohorts/my')
@advisor_required
def my_cohorts():
    cohorts = []
    for cohort in CohortFilter.get_cohorts_of_user_id(current_user.get_id()):
        cohort['isOwnedByCurrentUser'] = True
        cohorts.append(cohort)
    return tolerant_jsonify(cohorts)


@app.route('/api/cohorts/all')
@advisor_required
def all_cohorts():
    scope = get_query_scope(current_user)
    uids = AuthorizedUser.get_all_uids_in_scope(scope)
    cohorts_per_uid = dict((uid, []) for uid in uids)
    for cohort in CohortFilter.get_cohorts_owned_by_uids(uids):
        for uid in cohort['owners']:
            cohorts_per_uid[uid].append(cohort)
    api_json = []
    for uid, user in calnet.get_calnet_users_for_uids(app, uids).items():
        cohorts = cohorts_per_uid[uid]
        api_json.append({
            'user': user,
            'cohorts': sorted(cohorts, key=lambda c: c['name']),
        })
    api_json = sorted(api_json, key=lambda v: v['user']['name'] or f"UID: {v['user']['uid']}")
    return tolerant_jsonify(api_json)


@app.route('/api/cohort/<cohort_id>/students_with_alerts')
@advisor_required
def students_with_alerts(cohort_id):
    benchmark = get_benchmarker(f'cohort {cohort_id} students_with_alerts')
    benchmark('begin')
    offset = get_param(request.args, 'offset', 0)
    limit = get_param(request.args, 'limit', 50)
    cohort = CohortFilter.find_by_id(
        cohort_id,
        include_alerts_for_user_id=current_user.get_id(),
        include_students=False,
        alert_offset=offset,
        alert_limit=limit,
    )
    benchmark('fetched cohort')
    if cohort and _can_current_user_view_cohort(cohort):
        _decorate_cohort(cohort)
        students = cohort.get('alerts', [])
        alert_sids = [s['sid'] for s in students]
        alert_profiles = get_summary_student_profiles(alert_sids)
        benchmark('fetched student profiles')
        alert_profiles_by_sid = {p['sid']: p for p in alert_profiles}
        for student in students:
            student.update(alert_profiles_by_sid[student['sid']])
            # The enrolled units count is the one piece of term data we want to preserve.
            if student.get('term'):
                student['term'] = {'enrolledUnits': student['term'].get('enrolledUnits')}
    else:
        raise ResourceNotFoundError(f'No cohort found with identifier: {cohort_id}')
    benchmark('end')
    return tolerant_jsonify(students)


@app.route('/api/cohort/<cohort_id>')
@advisor_required
def get_cohort(cohort_id):
    benchmark = get_benchmarker(f'cohort {cohort_id} get_cohort')
    benchmark('begin')
    filter_keys = list(request.args.keys())
    order_by = get_param(request.args, 'orderBy', None)
    if is_unauthorized_search(filter_keys, order_by):
        raise ForbiddenRequestError('You are unauthorized to access student data managed by other departments')
    include_students = to_bool(get_param(request.args, 'includeStudents'))
    include_students = True if include_students is None else include_students
    offset = get_param(request.args, 'offset', 0)
    limit = get_param(request.args, 'limit', 50)
    benchmark('begin cohort filter query')
    cohort = CohortFilter.find_by_id(
        int(cohort_id),
        order_by=order_by,
        offset=int(offset),
        limit=int(limit),
        include_alerts_for_user_id=current_user.get_id(),
        include_profiles=True,
        include_students=include_students,
    )
    if cohort and _can_current_user_view_cohort(cohort):
        _decorate_cohort(cohort)
        benchmark('end')
        return tolerant_jsonify(cohort)
    else:
        raise ResourceNotFoundError(f'No cohort found with identifier: {cohort_id}')


@app.route('/api/cohort/get_students_per_filters', methods=['POST'])
@advisor_required
def get_cohort_per_filters():
    benchmark = get_benchmarker('cohort get_students_per_filters')
    benchmark('begin')
    params = request.get_json()
    filters = get_param(params, 'filters', [])
    if not filters:
        raise BadRequestError('API requires \'filters\'')
    include_students = to_bool(get_param(params, 'includeStudents'))
    include_students = True if include_students is None else include_students
    order_by = get_param(params, 'orderBy', None)
    offset = get_param(params, 'offset', 0)
    limit = get_param(params, 'limit', 50)
    filter_keys = list(map(lambda f: f['key'], filters))
    if is_unauthorized_search(filter_keys, order_by):
        raise ForbiddenRequestError('You are unauthorized to access student data managed by other departments')
    benchmark('begin phantom cohort query')
    cohort = _construct_phantom_cohort(
        filters=filters,
        order_by=order_by,
        offset=int(offset),
        limit=int(limit),
        include_alerts_for_user_id=current_user.get_id(),
        include_profiles=True,
        include_students=include_students,
    )
    _decorate_cohort(cohort)
    benchmark('end')
    return tolerant_jsonify(cohort)


@app.route('/api/cohort/download_csv_per_filters', methods=['POST'])
@advisor_required
def download_csv_per_filters():
    benchmark = get_benchmarker('cohort download_csv_per_filters')
    benchmark('begin')
    params = request.get_json()
    filters = get_param(params, 'filters', [])
    fieldnames = get_param(params, 'csvColumnsSelected', [])
    if not filters:
        raise BadRequestError('API requires \'filters\'')
    filter_keys = list(map(lambda f: f['key'], filters))
    if is_unauthorized_search(filter_keys):
        raise ForbiddenRequestError('You are unauthorized to access student data managed by other departments')
    cohort = _construct_phantom_cohort(
        filters=filters,
        offset=0,
        limit=None,
        include_profiles=False,
        include_sids=True,
        include_students=False,
    )
    return response_with_students_csv_download(sids=cohort['sids'], fieldnames=fieldnames, benchmark=benchmark)


@app.route('/api/cohort/create', methods=['POST'])
@advisor_required
def create_cohort():
    params = request.get_json()
    name = get_param(params, 'name', None)
    filters = get_param(params, 'filters', None)
    order_by = params.get('orderBy')
    # Authorization check
    filter_keys = list(map(lambda f: f['key'], filters))
    if is_unauthorized_search(filter_keys, order_by):
        raise ForbiddenRequestError('You are unauthorized to access student data managed by other departments')
    filter_criteria = _translate_filters_to_cohort_criteria(filters)
    if not name or not filter_criteria:
        raise BadRequestError('Cohort creation requires \'name\' and \'filters\'')
    cohort = CohortFilter.create(
        uid=current_user.get_uid(),
        name=name,
        filter_criteria=filter_criteria,
        order_by=order_by,
        include_alerts_for_user_id=current_user.get_id(),
    )
    _decorate_cohort(cohort)
    return tolerant_jsonify(cohort)


@app.route('/api/cohort/update', methods=['POST'])
@advisor_required
def update_cohort():
    params = request.get_json()
    cohort_id = int(params.get('id'))
    name = params.get('name')
    filters = params.get('filters')
    # Validation
    if not name and not filters:
        raise BadRequestError('Invalid request')
    if not CohortFilter.is_cohort_owned_by(cohort_id, current_user.get_id()):
        raise ForbiddenRequestError(f'Invalid or unauthorized request')
    filter_keys = list(map(lambda f: f['key'], filters))
    if is_unauthorized_search(filter_keys):
        raise ForbiddenRequestError('You are unauthorized to access student data managed by other departments')
    filter_criteria = _translate_filters_to_cohort_criteria(filters)
    updated = CohortFilter.update(
        cohort_id=cohort_id,
        name=name,
        filter_criteria=filter_criteria,
        include_students=False,
        include_alerts_for_user_id=current_user.get_id(),
    )
    _decorate_cohort(updated)
    return tolerant_jsonify(updated)


@app.route('/api/cohort/delete/<cohort_id>', methods=['DELETE'])
@advisor_required
def delete_cohort(cohort_id):
    if cohort_id.isdigit():
        cohort_id = int(cohort_id)
        if CohortFilter.is_cohort_owned_by(cohort_id, current_user.get_id()):
            CohortFilter.delete(cohort_id)
            return tolerant_jsonify({'message': f'Cohort deleted (id={cohort_id})'}), 200
        else:
            raise BadRequestError(f'User {current_user.get_uid()} does not own cohort with id={cohort_id}')
    else:
        raise ForbiddenRequestError(f'Programmatic deletion of canned cohorts is not allowed (id={cohort_id})')


@app.route('/api/cohort/filter_options/<cohort_owner_uid>', methods=['POST'])
@advisor_required
def all_cohort_filter_options(cohort_owner_uid):
    if cohort_owner_uid == 'me':
        cohort_owner_uid = current_user.get_uid()
    existing_filters = get_param(request.get_json(), 'existingFilters', [])
    return tolerant_jsonify(get_cohort_filter_options(cohort_owner_uid, existing_filters))


@app.route('/api/cohort/translate_to_filter_options/<cohort_owner_uid>', methods=['POST'])
@advisor_required
def translate_cohort_filter_to_menu(cohort_owner_uid):
    if cohort_owner_uid == 'me':
        cohort_owner_uid = current_user.get_uid()
    criteria = get_param(request.get_json(), 'criteria')
    return tolerant_jsonify(translate_to_filter_options(cohort_owner_uid, criteria))


def _decorate_cohort(cohort):
    owner_uids = [o['uid'] for o in cohort['owners']]
    cohort.update({'isOwnedByCurrentUser': current_user.get_uid() in owner_uids})


def _can_current_user_view_cohort(cohort):
    if current_user.is_admin or not cohort['owners']:
        return True
    cohort_dept_codes = {dept_code for o in cohort['owners'] for dept_code in o['deptCodes']}
    if len(cohort_dept_codes):
        user_dept_codes = dept_codes_where_advising(current_user)
        return len([c for c in user_dept_codes if c in cohort_dept_codes])
    else:
        return False


def _construct_phantom_cohort(filters, **kwargs):
    # A "phantom" cohort is an unsaved search.
    cohort = CohortFilter(
        name=f'phantom_cohort_{datetime.now().timestamp()}',
        filter_criteria=_translate_filters_to_cohort_criteria(filters),
    )
    return cohort.to_api_json(**kwargs)


def _translate_filters_to_cohort_criteria(filters):
    db_type_per_key = _get_filter_db_type_per_key()
    criteria = {}
    for row in filters:
        key = row['key']
        db_type = db_type_per_key[key]
        if db_type == 'boolean':
            criteria[key] = row['value']
        elif db_type in ['string[]', 'json[]']:
            if not criteria.get(key):
                criteria[key] = []
            criteria[key].append(row['value'])
    return criteria


def _get_filter_db_type_per_key():
    filter_type_per_key = {}
    for category in get_cohort_filter_options(current_user.get_uid()):
        for _filter in category:
            filter_type_per_key[_filter['key']] = _filter['type']['db']
    return filter_type_per_key
