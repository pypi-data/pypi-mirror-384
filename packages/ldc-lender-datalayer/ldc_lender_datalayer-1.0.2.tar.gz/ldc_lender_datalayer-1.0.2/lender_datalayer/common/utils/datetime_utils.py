"""
Data Layer DateTime Utilities Module

This module contains datetime utility functions used by data layer mappers.
Only includes utilities that are actually used in the data layer.
"""
import datetime

import pytz
from dateutil.parser import parse
from django.utils import timezone

from ..constants import DateFormat, TimeZone


def get_today_dtm():
    return datetime.datetime.today()


def get_todays_date():
    return datetime.date.today()


def get_current_dtm():
    try:
        return timezone.localtime(timezone.now())
    except Exception as e:
        return datetime.datetime.now()


def get_datetime_as_string(date_time=None, dtm_format=None):
    try:
        if not date_time:
            date_time = get_current_dtm()

        if type(date_time) == str:
            date_time = parse(date_time, dayfirst=True)

        if dtm_format:
            return date_time.strftime(dtm_format)

        return date_time.strftime("%Y-%m-%d %H:%M:%S.%f")
    except Exception:
        return None


def get_current_date(day=None, month=None, year=None):
    try:
        curr_date = get_current_dtm().date()
    except Exception as e:
        curr_date = get_current_dtm().date()

    curr_date = curr_date.replace(year=year or curr_date.year,
                                  month=month or curr_date.month,
                                  day=day or curr_date.day)
    return curr_date



def get_current_time_in_ist(date_time=None, dtm_format=None, dtm_result=False):
    """
        this method will take only UTC datetime,
        and it will convert UTC datetime to IST datetime format
    """
    try:
        if not date_time:
            date_time = datetime.datetime.now()

        if isinstance(date_time, str):
            date_time = parse(date_time)

        # Convert UTC time to IST (UTC + 5 hours 30 minutes)
        ist_time = date_time + datetime.timedelta(hours=5, minutes=30)
        if dtm_result:
            return ist_time

        if dtm_format:
            return ist_time.strftime(dtm_format)

        # Adding "%p" to include AM/PM indicator
        return ist_time.strftime("%Y-%m-%d %I:%M %p")
    except Exception:
        return None


def get_dtm_from_str(date_time_str, dtm_format=None):
    if not dtm_format:
        return parse(date_time_str, dayfirst=True)
    return datetime.datetime.strptime(date_time_str, dtm_format)


def get_date_from_request(date):
    return get_datetime_as_string(
        get_dtm_from_str(date, dtm_format="%d/%m/%Y"), dtm_format=DateFormat.YEAR_MONTH_DAY)



def get_todays_date_in_ist():
    utc_now = datetime.datetime.now()
    ist_tz = pytz.timezone('Asia/Kolkata')
    ist_date = utc_now.astimezone(ist_tz).date()
    return ist_date
