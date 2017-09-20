import math
from boac.externals import canvas
from flask import current_app as app
import pandas


def course_analytics_for_user(uid, canvas_user_id):
    analytics_per_course = []
    user_courses = canvas.get_user_courses(app.canvas_instance, uid)
    if user_courses:
        for course in user_courses:
            course_analytics = {
                'canvasCourseId': course['id'],
                'courseName': course['name'],
                'courseCode': course['course_code'],
            }
            student_summaries = canvas.get_student_summaries(app.canvas_instance, course['id'])
            if not student_summaries:
                course_analytics['analytics'] = {'error': 'Unable to retrieve analytics'}
            else:
                course_analytics['analytics'] = analytics_from_summary_feed(student_summaries, canvas_user_id, course)
            analytics_per_course.append(course_analytics)
    return analytics_per_course


def analytics_from_summary_feed(summary_feed, canvas_user_id, canvas_course):
    """Given a student summary feed for a Canvas course, return analytics for a given user"""
    df = pandas.DataFrame(summary_feed, columns=['id', 'page_views', 'participations', 'tardiness_breakdown'])
    df.fillna(0, inplace=True)
    df['on_time'] = df['tardiness_breakdown'].map(lambda t: t['on_time'])

    student_row = df.loc[df['id'].values == canvas_user_id]
    if not len(student_row):
        app.logger.error('Canvas ID {} not found in student summaries for course site {}'.format(canvas_user_id, canvas_course['id']))
        return {'error': 'Unable to retrieve analytics'}

    def analytics_for_column(column_name):
        column_zscore = zscore(df, student_row, column_name)
        return {
            'courseDeciles': quantiles(df[column_name], 10),
            'student': {
                'raw': student_row[column_name].values[0].item(),
                'zscore': column_zscore,
                'percentile': zptile(column_zscore),
            },
        }

    return {
        'assignmentsOnTime': analytics_for_column('on_time'),
        'pageViews': analytics_for_column('page_views'),
        'participations': analytics_for_column('participations'),
    }


def quantiles(series, count):
    """Return a given number of evenly spaced quantiles for a given series"""
    return [series.quantile(n / count) for n in range(0, count + 1)]


def zptile(z_score):
    """Derive percentile from zscore"""
    return 50 * (math.erf(z_score / 2 ** .5) + 1)


def zscore(dataframe, row, column_name):
    """Given a dataframe, an individual row, and column name, return a zscore for the value at that position"""
    return (row[column_name].values[0] - dataframe[column_name].mean()) / dataframe[column_name].std(ddof=0)