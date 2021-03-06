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

from decimal import Decimal
import io

from boac.externals import data_loch
from boac.lib.mockingdata import MockRows, register_mock
import pytest


@pytest.mark.usefixtures('db_session')
class TestDataLoch:

    def test_get_student_profiles(self, app):
        import json
        sid = '11667051'
        student_profiles = data_loch.get_student_profiles([sid])
        assert len(student_profiles) == 1

        student = student_profiles[0]
        assert student['sid'] == sid
        assert student['gender'] == 'Different Identity'
        assert student['minority'] is False
        sis_profile = json.loads(student_profiles[0]['profile'])['sisProfile']
        assert sis_profile['academicCareer'] == 'UGRD'

    def test_get_enrolled_primary_sections(self, app):
        sections = data_loch.get_enrolled_primary_sections('2178', 'MATH1')
        assert len(sections) == 6
        for section in sections:
            assert section['term_id'] == '2178'
            assert section['sis_course_name'].startswith('MATH 1')

    def test_get_term_gpas(self, app):
        term_gpas = data_loch.get_term_gpas(['11667051'])
        assert len(term_gpas) == 4
        assert term_gpas[0]['term_id'] == '2182'
        assert term_gpas[0]['sid'] == '11667051'
        assert term_gpas[0]['gpa'] == Decimal('2.900')
        assert term_gpas[0]['units_taken_for_gpa'] == 14
        assert term_gpas[3]['term_id'] == '2162'
        assert term_gpas[3]['sid'] == '11667051'
        assert term_gpas[3]['gpa'] == Decimal('3.800')
        assert term_gpas[3]['units_taken_for_gpa'] == 15

    def test_get_asc_advising_notes(self, app):
        notes = data_loch.get_asc_advising_notes('11667051')
        assert len(notes) == 2
        assert notes[0]['id'] == '11667051-139362'
        assert notes[0]['sid'] == '11667051'
        assert notes[0]['author_uid'] == '1133399'
        assert notes[0]['author_name'] == 'Lemmy Kilmister'
        assert notes[0]['created_at']
        assert notes[0]['updated_at']

    def test_get_e_i_advising_notes(self, app):
        """Excludes notes with author name 'Reception Front Desk'."""
        notes = data_loch.get_e_i_advising_notes('11667051')
        assert len(notes) == 1
        assert notes[0]['id'] == '11667051-151620'
        assert notes[0]['sid'] == '11667051'
        assert notes[0]['author_uid'] == '1133398'
        assert notes[0]['author_name'] == 'Charlie Christian'
        assert notes[0]['created_at']
        assert notes[0]['updated_at']

    def test_get_e_i_advising_note_topics(self, app):
        topics = data_loch.get_e_i_advising_note_topics('11667051')
        assert len(topics) == 2
        assert topics[0]['id'] == '11667051-151620'
        assert topics[0]['topic'] == 'Course Planning'

    def test_get_sis_advising_note_attachment(self, app):
        attachment = data_loch.get_sis_advising_note_attachment('11667051', '11667051_00001_1.pdf')
        assert len(attachment) == 1
        assert attachment[0]['advising_note_id'] == '11667051-00001'
        assert attachment[0]['created_by'] == 'UCBCONVERSION'
        assert attachment[0]['sis_file_name'] == '11667051_00001_1.pdf'
        assert attachment[0]['user_file_name'] == 'efac7b10-c3f2-11e4-9bbd-ab6a6597d26f.pdf'
        assert attachment[0]['is_historical'] is True

    def test_override_fixture(self, app):
        mr = MockRows(io.StringIO('sid,first_name,last_name\n20000000,Martin,Van Buren'))
        with register_mock(data_loch.get_sis_section_enrollments, mr):
            data = data_loch.get_sis_section_enrollments(2178, 12345)
        assert len(data) == 1
        assert {'sid': 20000000, 'first_name': 'Martin', 'last_name': 'Van Buren'} == data[0]

    def test_fixture_not_found(self, app):
        no_db = data_loch.get_sis_section_enrollments(0, 0)
        # TODO Real data_loch queries will return an empty list if the course is not found.
        assert no_db is None
