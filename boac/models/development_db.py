import csv
from boac import db, std_commit
from boac.models.athletics import Athletics
from boac.models.authorized_user import AuthorizedUser
from boac.models.cohort_filter import CohortFilter
from boac.models.student import Student
# Models below are included so that db.create_all will find them.
from boac.models.db_relationships import cohort_filter_owners, student_athletes # noqa
from boac.models.job_progress import JobProgress # noqa
from boac.models.json_cache import JsonCache # noqa
from boac.models.normalized_cache_student import NormalizedCacheStudent # noqa
from boac.models.normalized_cache_student_major import NormalizedCacheStudentMajor # noqa

_default_users_csv = """uid,is_admin,is_director,is_advisor
2040,true,false,false
53791,true,false,false
95509,true,false,false
177473,true,false,false
1133399,true,false,false
211159,true,false,false
242881,true,false,false
1022796,true,false,false
6446,false,true,true
"""

football_defensive_backs = {
    'group_code': 'MFB-DB',
    'group_name': 'Football, Defensive Backs',
    'team_code': 'FBM',
    'team_name': 'Football',
}
football_defensive_line = {
    'group_code': 'MFB-DL',
    'group_name': 'Football, Defensive Line',
    'team_code': 'FBM',
    'team_name': 'Football',
}
womens_field_hockey = {
    'group_code': 'WFH-AA',
    'group_name': 'Women\'s Field Hockey',
    'team_code': 'FHW',
    'team_name': 'Women\'s Field Hockey',
}
mens_tennis = {
    'group_code': 'MTE-AA',
    'group_name': 'Men\'s Tennis',
    'team_code': 'TNM',
    'team_name': 'Men\'s Tennis',
}
womens_tennis = {
    'group_code': 'WTE-AA',
    'group_name': 'Women\'s Tennis',
    'team_code': 'TNW',
    'team_name': 'Women\'s Tennis',
}


def clear():
    db.drop_all()


def load(cohort_test_data=False):
    load_schemas()
    load_development_data()
    if cohort_test_data:
        load_student_athletes()
        load_cohorts()
    return db


def load_schemas():
    """
    During early development, create the test DB from Python code.
    We will convert to SQL scripts before enabling production deployments.
    """
    db.create_all()


def load_development_data():
    csv_reader = csv.DictReader(_default_users_csv.splitlines())
    for row in csv_reader:
        # This script can be run more than once. Do not create user if s/he exists in BOAC db.
        user = AuthorizedUser.find_by_uid(row['uid'])
        if not user:
            user = AuthorizedUser(**row)
            db.session.add(user)
    std_commit()


def create_team_group(t):
    athletics = Athletics(group_code=t['group_code'], group_name=t['group_name'], team_code=t['team_code'],
                          team_name=t['team_name'])
    db.session.add(athletics)
    return athletics


def create_student(sid, uid, first_name, last_name, team_groups, gpa, level, units, majors, in_intensive_cohort=False):
    student = Student(
        sid=sid,
        uid=uid,
        first_name=first_name,
        last_name=last_name,
        in_intensive_cohort=in_intensive_cohort,
    )
    db.session.add(student)
    for team_group in team_groups:
        team_group.athletes.append(student)
    NormalizedCacheStudent.update_profile(sid, gpa=gpa, level=level, units=units)
    NormalizedCacheStudentMajor.update_majors(sid, majors)


def load_student_athletes():
    fdb = create_team_group(football_defensive_backs)
    fdl = create_team_group(football_defensive_line)
    mt = create_team_group(mens_tennis)
    wfh = create_team_group(womens_field_hockey)
    wt = create_team_group(womens_tennis)
    # Some students are on teams and some are not
    create_student(
        uid='61889',
        sid='11667051',
        first_name='Brigitte',
        last_name='Lin',
        team_groups=[wfh, wt],
        gpa=None,
        level=None,
        units=0,
        majors=['Economics BA'],
        in_intensive_cohort=True)
    create_student(
        uid='1022796',
        sid='8901234567',
        first_name='John',
        last_name='Crossman',
        team_groups=[],
        gpa='1.85',
        level='Freshman',
        units=12,
        majors=['Chemistry BS'],
        in_intensive_cohort=True)
    create_student(
        uid='2040',
        sid='2345678901',
        first_name='Oliver',
        last_name='Heyer',
        team_groups=[fdb, fdl],
        gpa='3.495',
        level='Junior',
        units=34,
        majors=['History BA'])
    create_student(
        uid='242881',
        sid='3456789012',
        first_name='Paul',
        last_name='Kerschen',
        team_groups=[fdl],
        gpa='3.005',
        level='Junior',
        units=70,
        majors=['English BA', 'Political Economy BA'],
        in_intensive_cohort=True)
    create_student(
        uid='1133399',
        sid='5678901234',
        first_name='Sandeep',
        last_name='Jayaprakash',
        team_groups=[fdb, fdl, mt],
        gpa='3.501',
        level='Senior',
        units=102,
        majors=['Letters & Sci Undeclared UG'])
    std_commit()


def load_cohorts():
    # Oliver's cohorts
    CohortFilter.create(uid='2040', label='All sports', group_codes=['MFB-DL', 'MFB-DL', 'WFH-AA'])
    CohortFilter.create(uid='2040', label='Football, Defense', group_codes=['MFB-DL', 'MFB-DL'])
    CohortFilter.create(uid='2040', label='Field Hockey', group_codes=['WFH-AA'])
    # Sandeep's cohorts
    CohortFilter.create(uid='1133399', label='All sports', group_codes=['MFB-DL', 'MFB-DL', 'WFH-AA'])
    CohortFilter.create(uid='1133399', label='Football, Defense Backs', group_codes=['MFB-DB'])
    std_commit()


if __name__ == '__main__':
    import boac.factory
    boac.factory.create_app()
    load()
