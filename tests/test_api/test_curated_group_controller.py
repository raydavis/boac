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

from boac.models.authorized_user import AuthorizedUser
from boac.models.curated_group import CuratedGroup
from boac.models.manually_added_advisee import ManuallyAddedAdvisee
import pytest
import simplejson as json


admin_uid = '2040'
asc_advisor_uid = '6446'
coe_advisor_uid = '1133399'
coe_scheduler_uid = '6972201'
asc_and_coe_advisor_uid = '90412'


@pytest.fixture()
def asc_advisor(fake_auth):
    fake_auth.login(asc_advisor_uid)


@pytest.fixture()
def asc_and_coe_advisor(fake_auth):
    fake_auth.login(asc_and_coe_advisor_uid)


@pytest.fixture()
def coe_advisor(fake_auth):
    fake_auth.login(coe_advisor_uid)


@pytest.fixture()
def coe_scheduler(fake_auth):
    fake_auth.login(coe_scheduler_uid)


@pytest.fixture()
def no_canvas_data_access_advisor(fake_auth):
    fake_auth.login('1')


@pytest.fixture()
def admin_user_session(fake_auth):
    fake_auth.login(admin_uid)


@pytest.fixture()
def admin_curated_groups():
    user = AuthorizedUser.find_by_uid(admin_uid)
    return CuratedGroup.get_curated_groups_by_owner_id(user.id)


@pytest.fixture()
def asc_curated_groups():
    advisor = AuthorizedUser.find_by_uid(asc_advisor_uid)
    return CuratedGroup.get_curated_groups_by_owner_id(advisor.id)


@pytest.fixture()
def coe_advisor_groups():
    advisor = AuthorizedUser.find_by_uid(coe_advisor_uid)
    return CuratedGroup.get_curated_groups_by_owner_id(advisor.id)


class TestGetCuratedGroup:
    """Curated Group API."""

    @staticmethod
    def _api_get_curated_group(
            client,
            curated_group_id,
            order_by='last_name',
            offset=0,
            limit=50,
            expected_status_code=200,
    ):
        response = client.get(f'/api/curated_group/{curated_group_id}?offset={offset}&limit={limit}&orderBy={order_by}')
        assert response.status_code == expected_status_code
        return response.json

    @staticmethod
    def _api_students_with_alerts(client, curated_group_id, expected_status_code=200):
        response = client.get(f'/api/curated_group/{curated_group_id}/students_with_alerts')
        assert response.status_code == expected_status_code
        return response.json

    def test_not_authenticated(self, asc_curated_groups, client):
        """Anonymous user is rejected."""
        self._api_get_curated_group(client, asc_curated_groups[0].id, expected_status_code=401)

    def test_unauthorized(self, asc_curated_groups, coe_advisor, client):
        """403 if user does not share a department membership with group owner."""
        self._api_get_curated_group(client, asc_curated_groups[0].id, expected_status_code=403)

    def test_advisor_cannot_see_admin_curated_group(self, admin_curated_groups, coe_advisor, client):
        """403 if user does not share a department membership with group owner."""
        self._api_get_curated_group(client, admin_curated_groups[0].id, expected_status_code=403)

    def test_curated_group_includes_alert_count(self, asc_advisor, asc_curated_groups, client, create_alerts):
        """Includes alert count per student."""
        api_json = self._api_get_curated_group(client, asc_curated_groups[0].id)
        students = api_json.get('students')
        assert students
        for student in students:
            assert isinstance(student.get('alertCount'), int)
        student_with_alerts = next((s for s in students if s['sid'] == '11667051'), None)
        assert student_with_alerts
        assert student_with_alerts['alertCount'] == 3

    def test_curated_group_includes_term_gpa(self, asc_advisor, asc_curated_groups, client):
        api_json = self._api_get_curated_group(client, asc_curated_groups[0].id)
        students = api_json['students']
        deborah = next(s for s in students if s['firstName'] == 'Deborah')
        assert len(deborah['termGpa']) == 4
        assert deborah['termGpa'][0] == {'termName': 'Spring 2018', 'gpa': 2.9}
        assert deborah['termGpa'][3] == {'termName': 'Spring 2016', 'gpa': 3.8}

    def test_view_permitted_shared_dept(self, asc_curated_groups, asc_and_coe_advisor, client):
        """Advisor can view group if they share the group owner's department memberships."""
        group = self._api_get_curated_group(client, asc_curated_groups[0].id)
        assert group['students']
        response = client.get(f'/api/curated_group/{asc_curated_groups[0].id}/students_with_alerts')
        assert response.status_code == 200

    def test_curated_group_includes_students_without_alerts(
            self,
            asc_advisor,
            asc_curated_groups,
            client,
            create_alerts,
    ):
        """Includes students in response."""
        api_json = self._api_get_curated_group(client, asc_curated_groups[0].id, order_by='first_name')
        last_names = [s.get('lastName') for s in api_json['students']]
        assert last_names == ['Davies', 'Farestveit', 'Kerschen', 'Jayaprakash']
        alert_counts = [s.get('alertCount') for s in api_json['students']]
        assert alert_counts == [3, 0, 1, 0]

    def test_order_by_level(self, asc_advisor, asc_curated_groups, client):
        """Includes students in response."""
        api_json = self._api_get_curated_group(client, asc_curated_groups[0].id, order_by='level', offset=1, limit=2)
        names = [f"{s.get('level')} ({s.get('lastName')})" for s in api_json['students']]
        assert names == ['Junior (Kerschen)', 'Senior (Farestveit)']

    def test_order_by_major(self, asc_advisor, asc_curated_groups, client):
        """Includes students in response."""
        api_json = self._api_get_curated_group(client, asc_curated_groups[0].id, order_by='major', offset=1)
        majors = [f"{s.get('majors')[0]} ({s.get('lastName')})" for s in api_json['students']]
        assert majors == [
            'English BA (Kerschen)',
            'Letters & Sci Undeclared UG (Jayaprakash)',
            'Nuclear Engineering BS (Farestveit)',
        ]

    def test_curated_group_detail_includes_profiles(self, asc_advisor, asc_curated_groups, client, create_alerts):
        """Returns all students with profile data."""
        api_json = self._api_get_curated_group(client, asc_curated_groups[0].id)
        student = api_json['students'][0]
        assert student['cumulativeGPA'] == 3.8
        assert student['cumulativeUnits'] == 101.3
        assert student['level'] == 'Junior'
        assert len(student['majors']) == 2

    def test_curated_group_detail_includes_athletics(self, asc_advisor, asc_curated_groups, client):
        """Returns athletics data, including intensive and inactive, for ASC advisors."""
        api_json = self._api_get_curated_group(client, asc_curated_groups[0].id)
        students = api_json['students']
        teams = students[0]['athleticsProfile']['athletics']
        assert len(teams) == 2
        assert teams[0]['name'] == 'Women\'s Field Hockey'
        assert teams[0]['groupCode'] == 'WFH'
        assert teams[1]['name'] == 'Women\'s Tennis'
        assert teams[1]['groupCode'] == 'WTE'
        assert students[0]['athleticsProfile']['inIntensiveCohort'] is True
        assert students[0]['athleticsProfile']['isActiveAsc'] is True
        assert students[0]['athleticsProfile']['statusAsc'] == 'Compete'

    def test_curated_group_detail_omits_athletics_non_asc(self, client, coe_advisor, coe_advisor_groups):
        """Returns team memberships only for non-ASC advisors."""
        api_json = self._api_get_curated_group(client, coe_advisor_groups[0].id)
        student = api_json['students'][0]
        assert len(student['athleticsProfile']['athletics']) == 1
        assert 'inIntensiveCohort' not in student['athleticsProfile']
        assert 'isActiveAsc' not in student['athleticsProfile']
        assert 'statusAsc' not in student['athleticsProfile']

    def test_curated_group_detail_includes_canvas_data(self, client, coe_advisor):
        group = _api_create_group(client, name='The Awkward Age', sids=['5678901234'])
        student_feed = self._api_get_curated_group(client, group['id'])['students'][0]
        assert 'analytics' in student_feed['term']['enrollments'][0]['canvasSites'][0]

    def test_curated_group_detail_suppresses_canvas_data_when_unauthorized(self, client, no_canvas_data_access_advisor):
        group = _api_create_group(client, name='The Awkward Age', sids=['5678901234'])
        student_feed = self._api_get_curated_group(client, group['id'])['students'][0]
        assert student_feed['term']['enrollments'][0]['canvasSites'] == []

    def test_students_with_alerts(self, asc_advisor, asc_curated_groups, client, create_alerts, db_session):
        """Students with alerts per group id."""
        api_json = self._api_students_with_alerts(client, asc_curated_groups[0].id)
        assert len(api_json) == 2
        assert api_json[0]['alertCount'] == 3
        assert api_json[1]['alertCount'] == 1

        student = client.get('/api/student/by_uid/61889').json
        alert_to_dismiss = student['notifications']['alert'][0]['id']
        client.get('/api/alerts/' + str(alert_to_dismiss) + '/dismiss')
        students_with_alerts = client.get(f'/api/curated_group/{asc_curated_groups[0].id}/students_with_alerts').json
        assert students_with_alerts[0]['alertCount'] == 2

    def test_group_includes_student_summary(self, asc_advisor, asc_curated_groups, client, create_alerts):
        """Returns summary details but not full term and analytics data."""
        api_json = self._api_students_with_alerts(client, asc_curated_groups[0].id)
        assert api_json[0]['cumulativeGPA'] == 3.8
        assert api_json[0]['cumulativeUnits'] == 101.3
        assert api_json[0]['expectedGraduationTerm']['name'] == 'Fall 2019'
        assert api_json[0]['level'] == 'Junior'
        assert api_json[0]['termGpa'][0]['gpa'] == 2.9
        assert len(api_json[0]['majors']) == 2

    def test_curated_groups_all(self, asc_and_coe_advisor, client):
        """Returns all groups to which user has viewing access, per owner."""
        response = client.get('/api/curated_groups/all')
        assert response.status_code == 200
        api_json = response.json
        print(api_json)
        count = len(api_json)
        for index, entry in enumerate(api_json):
            user = entry['user']
            if 0 < index < count and user['name'] and api_json[index - 1]['user']['name']:
                # Verify order
                assert user['name'] > api_json[index - 1]['user']['name']
            if user['uid'] == asc_advisor_uid or user['uid'] == coe_advisor_uid:
                assert len(entry['groups'])
                assert entry['groups'][0]['name']
                assert entry['groups'][0]['totalStudentCount']


class TestMyCuratedGroups:
    """Curated Group API."""

    @staticmethod
    def _api_my_curated_groups(client, expected_status_code=200):
        response = client.get('/api/curated_groups/my')
        assert response.status_code == expected_status_code
        return response.json

    @staticmethod
    def _api_my_curated_groups_by_sid(client, sid, expected_status_code=200):
        response = client.get(f'/api/curated_groups/my/{sid}')
        assert response.status_code == expected_status_code
        return response.json

    def test_not_authenticated(self, client):
        """Anonymous user is rejected."""
        self._api_my_curated_groups(client, expected_status_code=401)

    def test_coe_scheduler_not_allowed(self, client, coe_scheduler):
        """User who is_scheduler will be denied."""
        self._api_my_curated_groups(client, expected_status_code=401)

    def test_coe_curated_groups(self, client, coe_advisor):
        """Returns curated groups of COE advisor."""
        api_json = self._api_my_curated_groups(client)
        assert len(api_json) == 1
        group = api_json[0]
        assert 'id' in group
        assert 'alertCount' in group
        assert 'totalStudentCount' in group
        assert group['name'] == 'I have one student'

    def test_asc_curated_groups(self, asc_advisor, client):
        """Returns curated groups of ASC advisor."""
        api_json = self._api_my_curated_groups(client)
        group = api_json[0]
        assert group['name'] == 'Four students'
        assert group['totalStudentCount'] == 4

    def test_not_authenticated_curated_groups_by_sid(self, client):
        """Anonymous user is rejected."""
        assert self._api_my_curated_groups_by_sid(client, sid='7890123456', expected_status_code=401)

    def test_curated_groups_by_sid(self, client, coe_advisor, coe_advisor_groups):
        """API delivers accurate set of student SIDs."""
        sids = CuratedGroup.get_all_sids(curated_group_id=coe_advisor_groups[0].id)
        sample_sid = sids[0]
        assert self._api_my_curated_groups_by_sid(client, sid=sample_sid) == [coe_advisor_groups[0].id]


class TestAddStudents:
    """Curated Group API."""

    @staticmethod
    def _api_add_students(client, curated_group_id, expected_status_code=200, return_student_profiles=False, sids=()):
        response = client.post(
            '/api/curated_group/students/add',
            data=json.dumps({
                'curatedGroupId': curated_group_id,
                'returnStudentProfiles': return_student_profiles,
                'sids': sids,
            }),
            content_type='application/json',
        )
        assert response.status_code == expected_status_code
        return response.json

    def test_not_authenticated(self, asc_curated_groups, client):
        """Anonymous user is rejected."""
        assert self._api_add_students(client, asc_curated_groups[0].id, expected_status_code=401, sids=['2345678901'])

    def test_unauthorized(self, asc_curated_groups, admin_user_session, client):
        """403 if user does not own the group."""
        assert self._api_add_students(client, asc_curated_groups[0].id, expected_status_code=403, sids=['2345678901'])

    def test_add_student(self, asc_advisor, client):
        """Create a group and add a student."""
        group_name = 'Trams of Old London'
        group = _api_create_group(client, name=group_name)
        assert group['totalStudentCount'] == 0
        sid = '2345678901'
        updated_group = self._api_add_students(client, group['id'], sids=[sid])
        assert updated_group['name'] == group_name
        assert updated_group['totalStudentCount'] == 1
        assert updated_group['students'][0]['sid'] == sid

    def test_add_students(self, asc_advisor, client):
        """Create group and add students."""
        name = 'Cheap Tricks'
        group = _api_create_group(client, name=name, sids=['2345678901', '11667051'])
        assert group['name'] == name
        assert group['totalStudentCount'] == 2
        # Add students
        updated_group = self._api_add_students(
            client,
            group['id'],
            return_student_profiles=True,
            sids=['7890123456'],
        )
        assert updated_group['totalStudentCount'] == 3
        students = updated_group['students']
        sids = [s['sid'] for s in students]
        assert sids == ['11667051', '2345678901', '7890123456']
        # Add more and ask for FULL student profiles in payload
        updated_group = self._api_add_students(
            client,
            group['id'],
            return_student_profiles=True,
            sids=['890127492', '8901234567'],
        )
        assert updated_group['totalStudentCount'] == 5
        students = updated_group['students']
        students.sort(key=lambda s: s['sid'])
        student = students[0]
        assert student['sid'] == '11667051'
        assert student['canvasUserId'] == '9000100'
        for expected_key in ('cumulativeGPA', 'cumulativeGPA', 'cumulativeUnits', 'majors', 'termGpa'):
            assert expected_key in student, f'Failed to find {expected_key} in student'


class TestRemoveStudent:
    """Curated Group API."""

    def test_not_authenticated(self, asc_curated_groups, client):
        """Anonymous user is rejected."""
        response = client.delete(f'/api/curated_group/{asc_curated_groups[0].id}/remove_student/2345678901')
        assert response.status_code == 401

    def test_unauthorized(self, asc_curated_groups, admin_user_session, client):
        """403 if user does not own the group."""
        response = client.delete(f'/api/curated_group/{asc_curated_groups[0].id}/remove_student/2345678901')
        assert response.status_code == 403

    def test_remove_student(self, asc_advisor, client):
        """Remove student from a curated group."""
        name = 'Furry Green Atom Bowl'
        group = _api_create_group(client, name=name)
        group_id = group['id']
        sid = '2345678901'
        response = client.post(
            '/api/curated_group/students/add',
            data=json.dumps({'curatedGroupId': group_id, 'sids': [sid]}),
            content_type='application/json',
        )
        assert response.status_code == 200
        assert response.json['name'] == name
        assert response.json['totalStudentCount'] == 1
        response = client.delete(f'/api/curated_group/{group_id}/remove_student/{sid}')
        assert response.status_code == 200
        empty_group = response.json
        assert empty_group['name'] == name
        assert empty_group['totalStudentCount'] == 0


class TestUpdateCuratedGroup:
    """Curated Group API."""

    def test_rename_group(self, asc_advisor, client):
        """Rename curated group."""
        group = _api_create_group(client, name='The Bones In The Ground')
        new_name = 'My Favourite Buildings'
        group_id = group['id']
        response = client.post(
            '/api/curated_group/rename',
            data=json.dumps({
                'id': group_id,
                'name': new_name,
            }),
            content_type='application/json',
        )
        assert response.status_code == 200
        assert client.get(f'/api/curated_group/{group_id}').json['name'] == new_name


class TestDeleteCuratedGroup:
    """Curated Group API."""

    def test_not_authenticated(self, asc_curated_groups, client):
        """Anonymous user is rejected."""
        response = client.delete(f'/api/curated_group/delete/{asc_curated_groups[0].id}')
        assert response.status_code == 401

    def test_unauthorized(self, asc_curated_groups, admin_user_session, client):
        """403 if user does not own the group."""
        response = client.delete(f'/api/curated_group/delete/{asc_curated_groups[0].id}')
        assert response.status_code == 403

    def test_delete_group(self, asc_advisor, client):
        """Delete curated group."""
        group = _api_create_group(client, name='Mellow Together')
        group_id = group['id']
        assert client.delete(f'/api/curated_group/delete/{group_id}').status_code == 200
        assert client.get(f'/api/curated_group/{group_id}').status_code == 404


class TestCuratedGroupWithInactives:
    active_sid = '2345678901'
    inactive_sid = '3141592653'
    completed_sid = '2718281828'

    def test_create_group_with_inactives(self, asc_advisor, client):
        group = _api_create_group(
            client,
            200,
            "Brenda's Iron Sledge",
            [self.active_sid, self.inactive_sid, self.completed_sid],
        )
        group_id = group['id']
        assert group['totalStudentCount'] == 3
        assert len(group['students']) == 3
        sids = [r['sid'] for r in group['students']]
        assert self.active_sid in sids
        assert self.inactive_sid in sids
        assert self.completed_sid in sids

        group_feed = client.get(f'/api/curated_group/{group_id}').json
        assert group_feed['totalStudentCount'] == 3
        assert len(group_feed['students']) == 3
        assert group_feed['students'][1]['sid'] == self.completed_sid
        assert group_feed['students'][1]['academicCareerStatus'] == 'Completed'
        assert group_feed['students'][1]['fullProfilePending'] is True
        assert group_feed['students'][1]['degree']['dateAwarded'] == '2010-05-14'
        assert group_feed['students'][1]['degree']['description'] == 'Doctor of Philosophy'
        assert group_feed['students'][2]['sid'] == self.inactive_sid
        assert group_feed['students'][2]['academicCareerStatus'] == 'Inactive'
        assert group_feed['students'][2]['fullProfilePending'] is True

    def test_add_inactive_to_group(self, asc_advisor, client):
        group = _api_create_group(
            client,
            200,
            'Listening to the Higsons',
            [self.active_sid],
        )
        assert group['totalStudentCount'] == 1
        updated_group = TestAddStudents._api_add_students(
            client,
            group['id'],
            return_student_profiles=True,
            sids=[self.inactive_sid],
        )
        assert updated_group['totalStudentCount'] == 2
        assert updated_group['students'][0]['sid'] == self.active_sid
        assert updated_group['students'][1]['sid'] == self.inactive_sid

    def test_inactive_group_creation_creates_manually_added_advisee(self, client, fake_auth):
        assert len(ManuallyAddedAdvisee.query.all()) == 0
        fake_auth.login('2040')
        _api_create_group(
            client,
            200,
            'Madonna of the Wasps',
            [self.active_sid, self.inactive_sid, self.completed_sid],
        )
        manually_added_advisees = ManuallyAddedAdvisee.query.all()
        assert len(manually_added_advisees) == 2
        assert manually_added_advisees[0].sid == self.completed_sid
        assert manually_added_advisees[1].sid == self.inactive_sid


class TestDownloadCuratedGroupCSV:
    """Download Curated Group CSV API."""

    def test_download_csv_not_authenticated(self, asc_curated_groups, client):
        """Anonymous user is rejected."""
        data = {
            'csvColumnsSelected': [
                'first_name',
                'last_name',
                'sid',
            ],
        }
        response = client.post(
            f'/api/curated_group/{asc_curated_groups[0].id}/download_csv',
            data=json.dumps(data),
            content_type='application/json',
        )
        assert response.status_code == 401

    def test_download_csv_unauthorized(self, asc_curated_groups, coe_advisor, client):
        """403 if user does not share a department membership with group owner."""
        data = {
            'csvColumnsSelected': [
                'first_name',
                'last_name',
                'sid',
            ],
        }
        response = client.post(
            f'/api/curated_group/{asc_curated_groups[0].id}/download_csv',
            data=json.dumps(data),
            content_type='application/json',
        )
        assert response.status_code == 403

    def test_download_csv(self, asc_advisor, asc_curated_groups, client):
        """Advisor can download CSV with ALL students of group."""
        data = {
            'csvColumnsSelected': [
                'first_name',
                'last_name',
                'sid',
                'email',
                'phone',
                'majors',
                'level',
                'terms_in_attendance',
                'expected_graduation_date',
                'units_completed',
                'term_gpa',
                'cumulative_gpa',
                'program_status',
            ],
        }
        response = client.post(
            f'/api/curated_group/{asc_curated_groups[0].id}/download_csv',
            data=json.dumps(data),
            content_type='application/json',
        )
        assert response.status_code == 200
        assert 'csv' in response.content_type
        csv = str(response.data)
        for snippet in [
            'first_name,last_name,sid,email,phone,majors,level,terms_in_attendance,expected_graduation_date,units_completed,term_gpa,cumulative_gpa,\
program_status',
            'Deborah,Davies,11667051,barnburner@berkeley.edu,415/123-4567,English BA;Nuclear Engineering BS,Junior,5,Fall 2019,101.3,2.900,3.8,',
            'Paul,Kerschen,3456789012,doctork@berkeley.edu,415/123-4567,English BA;Political Economy BA,Junior,5,Fall 2019,70,3.200,3.005,',
            'Sandeep,Jayaprakash,5678901234,ilovela@berkeley.edu,415/123-4567,Letters & Sci Undeclared UG,Senior,5,Fall 2019,102,2.100,3.501,',
            'Paul,Farestveit,7890123456,qadept@berkeley.edu,415/123-4567,Nuclear Engineering BS,Senior,5,Spring 2020,110,,3.9,',
        ]:
            assert str(snippet) in csv

    def test_download_csv_shared_dept(self, asc_curated_groups, asc_and_coe_advisor, client):
        """Advisor can download CSV if they share the group owner's department memberships."""
        data = {
            'csvColumnsSelected': [
                'first_name',
                'last_name',
                'sid',
            ],
        }
        response = client.post(
            f'/api/curated_group/{asc_curated_groups[0].id}/download_csv',
            data=json.dumps(data),
            content_type='application/json',
        )
        assert response.status_code == 200
        assert 'csv' in response.content_type

    def test_download_csv_custom_columns(self, asc_advisor, asc_curated_groups, client):
        """Advisor can generate a CSV with the columns they want."""
        data = {
            'csvColumnsSelected': [
                'majors',
                'level',
                'terms_in_attendance',
                'expected_graduation_date',
                'units_completed',
                'term_gpa',
                'cumulative_gpa',
                'program_status',
            ],
        }
        response = client.post(
            f'/api/curated_group/{asc_curated_groups[0].id}/download_csv',
            data=json.dumps(data),
            content_type='application/json',
        )
        assert response.status_code == 200
        assert 'csv' in response.content_type
        csv = str(response.data)
        for snippet in [
            'majors,level,terms_in_attendance,expected_graduation_date,units_completed,term_gpa,cumulative_gpa,program_status',
            'English BA;Nuclear Engineering BS,Junior,5,Fall 2019,101.3,2.900,3.8,',
            'English BA;Political Economy BA,Junior,5,Fall 2019,70,3.200,3.005,',
            'Letters & Sci Undeclared UG,Senior,5,Fall 2019,102,2.100,3.501,',
            'Nuclear Engineering BS,Senior,5,Spring 2020,110,,3.9,',
        ]:
            assert str(snippet) in csv


def _api_create_group(client, expected_status_code=200, name=None, sids=()):
    response = client.post(
        '/api/curated_group/create',
        data=json.dumps({
            'name': name,
            'sids': sids,
        }),
        content_type='application/json',
    )
    assert response.status_code == expected_status_code
    return response.json
