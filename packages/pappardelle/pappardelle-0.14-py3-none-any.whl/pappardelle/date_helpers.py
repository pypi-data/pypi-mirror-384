from datetime import datetime, timedelta, date


def days_before_at_this_time(x, ref_date=datetime.now()):
    return ref_date - timedelta(days=x)


def days_ago_at_this_time(x, ref_date=datetime.now()):
    return days_before_at_this_time(x, ref_date)


def days_after_at_this_time(x, ref_date=datetime.now()):
    return ref_date + timedelta(days=x)


def days_since_at_this_time(x, ref_date=datetime.now()):
    return days_after_at_this_time(x, ref_date)


def tomorrow_at_this_time():
    return datetime.now() + timedelta(days=1)


def yesterday_at_this_time():
    return datetime.now() - timedelta(days=1)


def days_before(x, ref_date=date.today()):
    return ref_date - timedelta(days=x)


# Alias for days_before
def days_ago(x):
    return days_before(x)


def days_after(x, ref_date=date.today()):
    return ref_date + timedelta(days=x)


# Alias for days_after
def days_since(x, ref_date=date.today()):
    return days_after(x, ref_date)


def tomorrow():
    return date.today() + timedelta(days=1)


def yesterday():
    return date.today() - timedelta(days=1)


def hours_before(x, ref_date=datetime.now()):
    return ref_date - timedelta(hours=x)


# Alias for hours_before
def hours_ago(x):
    return hours_before(x)


def hours_after(x, ref_date=datetime.now()):
    return ref_date + timedelta(hours=x)


# Alias for hours_after
def hours_since(x, ref_date=datetime.now()):
    return hours_after(x, ref_date)


def minutes_before(x, ref_date=datetime.now()):
    return ref_date - timedelta(minutes=x)


# Alias for minutes_before
def minutes_ago(x):
    return minutes_before(x)


def minutes_after(x, ref_date=datetime.now()):
    return ref_date + timedelta(minutes=x)


# Alias for minutes_after
def minutes_since(x, ref_date=datetime.now()):
    return minutes_after(x, ref_date)


def seconds_before(x, ref_date=datetime.now()):
    return ref_date - timedelta(minutes=x)


# Alias for seconds_before
def seconds_ago(x):
    return seconds_before(x)


def seconds_after(x, ref_date=datetime.now()):
    return ref_date + timedelta(minutes=x)


# Alias for seconds_after
def seconds_since(x, ref_date=datetime.now()):
    return seconds_after(x, ref_date)


def weeks_before(x, ref_date=date.today()):
    return ref_date - timedelta(weeks=x)


def weeks_before_at_this_time(x, ref_date=datetime.now()):
    return ref_date - timedelta(weeks=x)


def weeks_ago_at_this_time(x, ref_date=datetime.now()):
    return weeks_before_at_this_time(x, ref_date)


def weeks_after_at_this_time(x, ref_date=datetime.now()):
    return ref_date + timedelta(weeks=x)


def weeks_since_at_this_time(x, ref_date=datetime.now()):
    return weeks_after_at_this_time(x, ref_date)


# Alias for seconds_before
def weeks_ago(x):
    return weeks_before(x)


def weeks_after(x, ref_date=date.today()):
    return ref_date + timedelta(weeks=x)


# Alias for seconds_after
def weeks_since(x, ref_date=date.today()):
    return weeks_after(x, ref_date)


# Internal method to support the month_* functions
def month_add(x, ref_date=date.today()):
    years_to_add = int((ref_date.month + x) / 12)
    months_to_set = (ref_date.month + x) % 12
    if type(ref_date) is datetime:
        return datetime(ref_date.year + years_to_add, months_to_set, ref_date.day, ref_date.hour, ref_date.minute, ref_date.second, ref_date.microsecond)
    elif type(ref_date) is date:
        return date(ref_date.year + years_to_add, months_to_set, ref_date.day)


def months_before(x, ref_date=date.today()):
    return month_add(-1*x, ref_date)


# Alias for months_before
def months_ago(x):
    return months_before(x)


def months_before_at_this_time(x, ref_date=datetime.now()):
    return month_add(-1*x, ref_date)


def months_ago_at_this_time(x, ref_date=datetime.now()):
    return months_before_at_this_time(x, ref_date)


def months_after_at_this_time(x, ref_date=datetime.now()):
    return month_add(x, ref_date)


def months_since_at_this_time(x, ref_date=datetime.now()):
    return months_after_at_this_time(x, ref_date)


def months_after(x, ref_date=date.today()):
    return month_add(x, ref_date)


# Alias for months_after
def months_since(x, ref_date=date.today()):
    return months_after(x, ref_date)


def years_before(x, ref_date=date.today()):
    if type(ref_date) is datetime:
        return datetime(ref_date.year - x, ref_date.month, ref_date.day, ref_date.hour, ref_date.minute, ref_date.second, ref_date.microsecond)
    elif type(ref_date) is date:
        return date(ref_date.year - x, ref_date.month, ref_date.day)


# Alias for years_before
def years_ago(x):
    return years_before(x)


def years_after(x, ref_date=date.today()):
    return years_before(-x, ref_date)


# Alias for years_after
def years_since(x, ref_date=date.today()):
    return years_after(x, ref_date)


def years_before_at_this_time(x, ref_date=datetime.now()):
    return years_before(x, ref_date)


def years_ago_at_this_time(x, ref_date=datetime.now()):
    return years_before_at_this_time(x, ref_date)


def years_after_at_this_time(x, ref_date=datetime.now()):
    return years_after(x, ref_date)


def years_since_at_this_time(x, ref_date=datetime.now()):
    return years_after_at_this_time(x, ref_date)

