from boac.externals import import_asc_athletes
from boac.models.athletics import Athletics


class TestImportAscAthletes:
    """Import ASC data"""

    def test_empty_import(self, app):
        """gracefully handles empty dataset"""
        athletics, students = import_asc_athletes.load_student_athletes(app, [])
        assert not athletics
        assert not students

    def test_students_on_multiple_teams(self, app):
        """maps one student to more than one team"""
        jane_sid = '1234567890'
        polo_code = 'WWP-AA'
        volleyball_code = 'WVB-AA'
        asc_data = [
            asc_data_row(jane_sid, 'Jane B. Sporty', polo_code, 'Women\'s Water Polo', 'MBB',
                         'Women\'s Water Polo', '2017-18', 'Yes'),
            asc_data_row(jane_sid, 'Jane B. Sporty', volleyball_code, 'Women\'s Volleyball', 'WVB',
                         'Women\'s Volleyball', '2017-18', 'Yes'),
        ]
        # Run import script
        athletics, students = import_asc_athletes.load_student_athletes(app, asc_data)
        assert 2 == len(athletics)
        assert 1 == len(students)
        # Verify results
        polo_team = Athletics.query.filter_by(group_code=polo_code).first()
        assert find_athlete(polo_team, jane_sid)
        volleyball_team = Athletics.query.filter_by(group_code=volleyball_code).first()
        assert find_athlete(volleyball_team, jane_sid)


def find_athlete(team, sid):
    return next(athlete for athlete in team.athletes if athlete.sid == sid)


def asc_data_row(sid, name, group_code, group_name, asc_code, team_name, academic_yr, is_active):
    return {
        'SID': sid,
        'cName': name,
        'SportCode': group_code,
        'Sport': group_name,
        'cSportCodeCore': asc_code,
        'acSportCore': team_name,
        'AcadYr': academic_yr,
        'SportActiveYN': is_active,
    }