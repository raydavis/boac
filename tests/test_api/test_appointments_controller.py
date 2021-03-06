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

from boac.models.appointment import Appointment
from boac.models.appointment_read import AppointmentRead
from boac.models.authorized_user import AuthorizedUser
from boac.models.drop_in_advisor import DropInAdvisor
import simplejson as json
from sqlalchemy import and_
from tests.util import override_config

coe_advisor_uid = '90412'
coe_drop_in_advisor_uid = '90412'
coe_scheduler_uid = '6972201'
l_s_college_advisor_uid = '188242'
l_s_college_drop_in_advisor_uid = '53791'
l_s_college_scheduler_uid = '19735'


class AppointmentTestUtil:

    @classmethod
    def create_appointment(cls, client, dept_code, details='', advisor_uid=None, expected_status_code=200):
        data = {
            'advisorUid': advisor_uid,
            'appointmentType': 'Drop-in',
            'deptCode': dept_code,
            'details': details,
            'sid': '3456789012',
            'topics': ['Topic for appointments, 1', 'Topic for appointments, 4'],
        }
        response = client.post(
            '/api/appointments/create',
            data=json.dumps(data),
            content_type='application/json',
        )
        assert response.status_code == expected_status_code
        return response.json


class TestCreateAppointment:

    @classmethod
    def _get_waitlist(cls, client, dept_code, expected_status_code=200):
        response = client.get(f'/api/appointments/waitlist/{dept_code}')
        assert response.status_code == expected_status_code
        if response.status_code == 200:
            return response.json['waitlist']

    def test_create_not_authenticated(self, client):
        """Returns 401 if not authenticated."""
        AppointmentTestUtil.create_appointment(client, 'COENG', expected_status_code=401)

    def test_create_appointment_as_coe_scheduler(self, client, fake_auth):
        """Scheduler can create appointments."""
        fake_auth.login(coe_scheduler_uid)
        details = 'Aloysius has some questions.'
        appointment = AppointmentTestUtil.create_appointment(client, 'COENG', details)
        appointment_id = appointment['id']
        waitlist = self._get_waitlist(client, 'COENG')
        matching = next((a for a in waitlist if a['details'] == details), None)
        assert matching
        assert appointment_id == matching['id']
        assert appointment['read'] is True
        assert appointment['status'] == 'waiting'
        assert appointment['student']['sid'] == '3456789012'
        assert appointment['student']['name'] == 'Paul Kerschen'
        assert appointment['student']['photoUrl']
        assert appointment['appointmentType'] == 'Drop-in'
        assert len(appointment['topics']) == 2
        # Verify that a deleted appointment is off the waitlist
        Appointment.delete(appointment_id)
        waitlist = self._get_waitlist(client, 'COENG')
        assert next((a for a in waitlist if a['details'] == details), None) is None

    def test_create_pre_reserved_appointment_for_specific_advisor(self, client, fake_auth):
        fake_auth.login(coe_scheduler_uid)
        details = 'Aloysius has some questions.'
        appointment = AppointmentTestUtil.create_appointment(client, 'COENG', details, advisor_uid=coe_drop_in_advisor_uid)
        appointment_id = appointment['id']
        waitlist = self._get_waitlist(client, 'COENG')
        matching = next((a for a in waitlist if a['details'] == details), None)
        assert appointment_id == matching['id']
        assert appointment['read'] is True
        assert appointment['status'] == 'reserved'
        assert appointment['advisorUid'] == coe_drop_in_advisor_uid
        assert appointment['statusBy']['uid'] == coe_drop_in_advisor_uid

    def test_other_departments_forbidden(self, client, fake_auth):
        fake_auth.login(coe_scheduler_uid)
        AppointmentTestUtil.create_appointment(client, 'UWASC', expected_status_code=403)

    def test_nonsense_department_not_found(self, client, fake_auth):
        fake_auth.login(coe_scheduler_uid)
        AppointmentTestUtil.create_appointment(client, 'DINGO', expected_status_code=404)

    def test_feature_flag(self, client, fake_auth, app):
        """Returns 404 if the Appointments feature is false."""
        with override_config(app, 'FEATURE_FLAG_ADVISOR_APPOINTMENTS', False):
            fake_auth.login(coe_advisor_uid)
            self._get_waitlist(client, 'COENG', expected_status_code=401)


class TestGetAppointment:

    @classmethod
    def _get_appointment(cls, client, appointment_id, expected_status_code=200):
        response = client.get(f'/api/appointments/{appointment_id}')
        assert response.status_code == expected_status_code
        return response.json

    def test_not_authenticated(self, client):
        """Returns 401 if not authenticated."""
        self._get_appointment(client, 'COENG', expected_status_code=401)

    def test_not_authorized(self, client, fake_auth):
        """Returns 401 if user is scheduler."""
        fake_auth.login(coe_scheduler_uid)
        self._get_appointment(client, 1, 401)

    def test_get_appointment(self, client, fake_auth):
        """Get appointment."""
        fake_auth.login(coe_advisor_uid)
        appointment = self._get_appointment(client, 1)
        assert appointment
        assert appointment['id'] == 1
        assert appointment['status'] is not None

    def test_feature_flag(self, client, fake_auth, app):
        """Returns 404 if the Appointments feature is false."""
        with override_config(app, 'FEATURE_FLAG_ADVISOR_APPOINTMENTS', False):
            fake_auth.login(coe_advisor_uid)
            self._get_appointment(client, 'COENG', expected_status_code=401)


class TestAppointmentCancel:

    @classmethod
    def _cancel_appointment(
            cls,
            client,
            appointment_id,
            cancel_reason,
            cancel_reason_explained=None,
            expected_status_code=200,
    ):
        data = {
            'cancelReason': cancel_reason,
            'cancelReasonExplained': cancel_reason_explained,
        }
        response = client.post(
            f'/api/appointments/{appointment_id}/cancel',
            data=json.dumps(data),
            content_type='application/json',
        )
        assert response.status_code == expected_status_code
        return response.json

    def test_mark_read_not_authenticated(self, client):
        """Returns 401 if not authenticated."""
        self._cancel_appointment(client, 1, 'Canceled by student', expected_status_code=401)

    def test_deny_advisor(self, app, client, fake_auth):
        """Returns 401 if user is an advisor without drop_in responsibilities."""
        fake_auth.login(l_s_college_advisor_uid)
        self._cancel_appointment(client, 1, 'Canceled by advisor', expected_status_code=401)

    def test_appointment_cancel(self, app, client, fake_auth):
        """Drop-in advisor can cancel appointment."""
        dept_code = 'QCADV'
        advisor = DropInAdvisor.advisors_for_dept_code(dept_code)[0]
        user = AuthorizedUser.find_by_id(advisor.authorized_user_id)
        fake_auth.login(user.uid)
        waiting = AppointmentTestUtil.create_appointment(client, dept_code)
        appointment = self._cancel_appointment(client, waiting['id'], 'Canceled by wolves')
        appointment_id = appointment['id']
        assert appointment_id == waiting['id']
        assert appointment['status'] == 'canceled'
        assert appointment['statusBy']['id'] == user.id
        assert appointment['statusBy']['uid'] == user.uid
        assert appointment['statusDate'] is not None
        Appointment.delete(appointment_id)

    def test_feature_flag(self, client, fake_auth, app):
        """Appointments feature is false."""
        dept_code = 'QCADV'
        advisor = DropInAdvisor.advisors_for_dept_code(dept_code)[0]
        fake_auth.login(AuthorizedUser.find_by_id(advisor.authorized_user_id).uid)
        appointment = AppointmentTestUtil.create_appointment(client, dept_code)
        with override_config(app, 'FEATURE_FLAG_ADVISOR_APPOINTMENTS', False):
            self._cancel_appointment(
                client,
                appointment_id=appointment['id'],
                cancel_reason='Canceled by the power of the mind',
                expected_status_code=401,
            )


class TestAppointmentCheckIn:

    @classmethod
    def _check_in(cls, client, appointment_id, expected_status_code=200):
        response = client.post(
            f'/api/appointments/{appointment_id}/check_in',
            content_type='application/json',
        )
        assert response.status_code == expected_status_code
        return response.json

    def test_not_authenticated(self, client):
        """Returns 401 if not authenticated."""
        self._check_in(client, 1, expected_status_code=401)

    def test_deny_advisor(self, app, client, fake_auth):
        """Returns 401 if user is not a drop-in advisor."""
        fake_auth.login(l_s_college_advisor_uid)
        self._check_in(client, 1, expected_status_code=401)

    def test_feature_flag(self, client, fake_auth, app):
        """Appointments feature is false."""
        dept_code = 'QCADV'
        advisor = DropInAdvisor.advisors_for_dept_code(dept_code)[0]
        fake_auth.login(AuthorizedUser.find_by_id(advisor.authorized_user_id).uid)
        appointment = AppointmentTestUtil.create_appointment(client, dept_code)
        with override_config(app, 'FEATURE_FLAG_ADVISOR_APPOINTMENTS', False):
            self._check_in(client, appointment['id'], expected_status_code=401)


class TestAppointmentReserve:

    @classmethod
    def _reserve_appointment(cls, client, appointment_id, expected_status_code=200):
        response = client.get(f'/api/appointments/{appointment_id}/reserve')
        assert response.status_code == expected_status_code
        return response.json

    @classmethod
    def _unreserve_appointment(cls, client, appointment_id, expected_status_code=200):
        response = client.get(f'/api/appointments/{appointment_id}/unreserve')
        assert response.status_code == expected_status_code
        return response.json

    def test_not_authenticated(self, client):
        """Returns 401 if not authenticated."""
        self._reserve_appointment(client, 1, expected_status_code=401)
        self._unreserve_appointment(client, 1, expected_status_code=401)

    def test_deny_advisor(self, app, client, fake_auth):
        """Returns 401 if user is not a drop-in advisor."""
        fake_auth.login(l_s_college_advisor_uid)
        self._reserve_appointment(client, 1, expected_status_code=401)
        self._unreserve_appointment(client, 1, expected_status_code=401)

    def test_unreserve_appointment_reserved_by_other(self, app, client, fake_auth):
        """Returns 401 if user un-reserves an appointment which is reserved by another."""
        waiting = Appointment.query.filter(
            and_(Appointment.status == 'waiting', Appointment.deleted_at == None),
        ).first()  # noqa: E711
        advisor = AuthorizedUser.find_by_id(waiting.created_by)
        fake_auth.login(advisor.uid)
        self._reserve_appointment(client, waiting.id)
        fake_auth.login(l_s_college_advisor_uid)
        self._unreserve_appointment(client, 1, expected_status_code=401)

    def test_reserve_appointment(self, app, client, fake_auth):
        """Drop-in advisor can reserve an appointment."""
        dept_code = 'QCADV'
        advisor = DropInAdvisor.advisors_for_dept_code(dept_code)[0]
        user = AuthorizedUser.find_by_id(advisor.authorized_user_id)
        fake_auth.login(user.uid)
        waiting = AppointmentTestUtil.create_appointment(client, dept_code)
        appointment = self._reserve_appointment(client, waiting['id'])
        assert appointment['status'] == 'reserved'
        assert appointment['statusDate'] is not None
        assert appointment['statusBy']['id'] == user.id
        Appointment.delete(appointment['id'])

    def test_steal_appointment_reservation(self, app, client, fake_auth):
        """Reserve an appointment that another advisor has reserved."""
        dept_code = 'COENG'
        advisor_1 = DropInAdvisor.advisors_for_dept_code(dept_code)[0]
        user_1 = AuthorizedUser.find_by_id(advisor_1.authorized_user_id)
        fake_auth.login(user_1.uid)
        waiting = AppointmentTestUtil.create_appointment(client, dept_code)
        appointment = self._reserve_appointment(client, waiting['id'])
        assert appointment['status'] == 'reserved'
        assert appointment['statusDate'] is not None
        assert appointment['statusBy']['id'] == user_1.id
        client.get('/api/auth/logout')

        # Another advisor comes along...
        advisor_2 = DropInAdvisor.advisors_for_dept_code(dept_code)[1]
        user_2 = AuthorizedUser.find_by_id(advisor_2.authorized_user_id)
        fake_auth.login(user_2.uid)
        appointment = self._reserve_appointment(client, waiting['id'])
        assert appointment['status'] == 'reserved'
        assert appointment['statusDate'] is not None
        assert appointment['statusBy']['id'] == user_2.id
        # Clean up
        Appointment.delete(appointment['id'])

    def test_unreserve_appointment(self, app, client, fake_auth):
        """Drop-in advisor can un-reserve an appointment."""
        dept_code = 'QCADV'
        advisor = DropInAdvisor.advisors_for_dept_code(dept_code)[0]
        user = AuthorizedUser.find_by_id(advisor.authorized_user_id)
        fake_auth.login(user.uid)
        waiting = AppointmentTestUtil.create_appointment(client, dept_code)
        reserved = self._reserve_appointment(client, waiting['id'])
        assert reserved['status'] == 'reserved'
        assert reserved['statusDate']
        assert reserved['statusBy']['id'] == user.id
        assert reserved['statusBy']['uid'] == user.uid
        assert 'name' in reserved['statusBy']
        appointment = self._unreserve_appointment(client, waiting['id'])
        assert appointment['status'] == 'waiting'
        assert appointment['statusDate'] is not None
        assert appointment['statusBy']['id'] == user.id
        Appointment.delete(appointment['id'])

    def test_feature_flag(self, client, fake_auth, app):
        """Appointments feature is false."""
        dept_code = 'QCADV'
        advisor = DropInAdvisor.advisors_for_dept_code(dept_code)[0]
        fake_auth.login(AuthorizedUser.find_by_id(advisor.authorized_user_id).uid)
        appointment = AppointmentTestUtil.create_appointment(client, dept_code)
        with override_config(app, 'FEATURE_FLAG_ADVISOR_APPOINTMENTS', False):
            self._reserve_appointment(client, appointment['id'], expected_status_code=401)


class TestAppointmentWaitlist:

    @classmethod
    def _get_waitlist(cls, client, dept_code, expected_status_code=200):
        response = client.get(f'/api/appointments/waitlist/{dept_code}')
        assert response.status_code == expected_status_code
        if response.status_code == 200:
            return response.json['waitlist']

    def test_mark_read_not_authenticated(self, client):
        """Returns 401 if not authenticated."""
        self._get_waitlist(client, 'COENG', expected_status_code=401)

    def test_unrecognized_dept_code(self, app, client, fake_auth):
        """Returns 404 if requested dept_code is invalid."""
        fake_auth.login(l_s_college_scheduler_uid)
        self._get_waitlist(client, 'BOGUS', expected_status_code=404)

    def test_deny_advisor(self, app, client, fake_auth):
        """Returns 401 if user is not a drop-in advisor."""
        fake_auth.login(l_s_college_advisor_uid)
        self._get_waitlist(client, 'QCADV', expected_status_code=401)

    def test_l_and_s_advisor_cannot_view_coe_waitlist(self, app, client, fake_auth):
        """L&S advisor cannot view COE appointments (waitlist)."""
        fake_auth.login(l_s_college_scheduler_uid)
        self._get_waitlist(client, 'COENG', expected_status_code=403)

    def test_coe_scheduler_waitlist(self, app, client, fake_auth):
        """Waitlist is properly sorted for COE drop-in advisor."""
        fake_auth.login(coe_drop_in_advisor_uid)
        waitlist = self._get_waitlist(client, 'COENG')
        assert len(waitlist) > 6
        # Appointments reserved by me are always on top
        assert waitlist[0]['status'] == 'reserved'
        assert waitlist[0]['statusBy']['uid'] == coe_drop_in_advisor_uid
        # Canceled appointments are put to the bottom of list
        assert waitlist[-1]['status'] == 'canceled'
        for index in range(1, len(waitlist) - 1):
            # Everything else is in between
            assert waitlist[index]['status'] in ('waiting', 'checked_in')

    def test_waitlist_include_checked_in_and_canceled(self, app, client, fake_auth):
        """For scheduler, the waitlist has appointments with event type 'waiting' or 'reserved'."""
        fake_auth.login(coe_scheduler_uid)
        appointments = self._get_waitlist(client, 'COENG')
        assert len(appointments) > 2
        for index, appointment in enumerate(appointments):
            if index > 0 and appointments[index - 1]['status'] == 'canceled':
                # Canceled appointments are put to the bottom of list
                assert appointment['status'] == 'canceled'
            else:
                assert appointment['status'] in ('waiting', 'reserved')

    def test_l_and_s_advisor_waitlist(self, app, client, fake_auth):
        """L&S advisor can only see L&S appointments."""
        fake_auth.login(l_s_college_scheduler_uid)
        appointments = self._get_waitlist(client, 'QCADV')
        assert len(appointments) == 2

    def test_l_s_college_drop_in_advisor_uid_waitlist(self, app, client, fake_auth):
        """L&S drop-in advisor can only see L&S appointments."""
        fake_auth.login(l_s_college_drop_in_advisor_uid)
        dept_code = 'QCADV'
        appointments = self._get_waitlist(client, dept_code)
        assert len(appointments) > 2
        for appointment in appointments:
            assert appointment['deptCode'] == dept_code

    def test_feature_flag(self, client, fake_auth, app):
        """Appointments feature is false."""
        with override_config(app, 'FEATURE_FLAG_ADVISOR_APPOINTMENTS', False):
            fake_auth.login(l_s_college_scheduler_uid)
            self._get_waitlist(client, 'COENG', expected_status_code=401)


class TestMarkAppointmentRead:

    @classmethod
    def _mark_appointment_read(cls, client, appointment_id, expected_status_code=200):
        response = client.post(
            f'/api/appointments/{appointment_id}/mark_read',
            data=json.dumps({'appointmentId': appointment_id}),
            content_type='application/json',
        )
        assert response.status_code == expected_status_code
        return response.json

    def test_mark_read_not_authenticated(self, client):
        """Returns 401 if not authenticated."""
        self._mark_appointment_read(client, 1, expected_status_code=401)

    def test_advisor_read_appointment(self, app, client, fake_auth):
        """L&S advisor reads an appointment."""
        fake_auth.login(l_s_college_scheduler_uid)
        # As scheduler, create appointment
        appointment = AppointmentTestUtil.create_appointment(client, 'QCADV')
        appointment_id = appointment['id']
        client.get('/api/auth/logout')
        # Verify unread by advisor
        uid = l_s_college_advisor_uid
        user_id = AuthorizedUser.get_id_per_uid(uid)
        assert AppointmentRead.was_read_by(user_id, appointment_id) is False
        # Next, log in as advisor and read the appointment
        fake_auth.login(uid)
        api_json = self._mark_appointment_read(client, appointment_id)
        assert api_json['appointmentId'] == appointment_id
        assert api_json['viewerId'] == user_id
        assert AppointmentRead.was_read_by(user_id, appointment_id) is True
        Appointment.delete(appointment_id)


class TestAuthorSearch:

    def test_find_appointment_advisors_by_name(self, client, fake_auth):
        fake_auth.login(coe_advisor_uid)
        response = client.get('/api/appointments/advisors/find_by_name?q=Jo')
        assert response.status_code == 200
        assert len(response.json) == 1
        labels = [s['label'] for s in response.json]
        assert 'Johnny C. Lately' in labels

    def test_feature_flag(self, client, fake_auth, app):
        """Appointments feature is false."""
        with override_config(app, 'FEATURE_FLAG_ADVISOR_APPOINTMENTS', False):
            fake_auth.login(coe_advisor_uid)
            response = client.get('/api/appointments/advisors/find_by_name?q=Jo')
            assert response.status_code == 401
