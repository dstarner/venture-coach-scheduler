from django.utils.dateparse import parse_datetime
from django.utils.timezone import is_aware, make_aware
import datetime
import pytz
from dateutil.relativedelta import relativedelta


def get_post(request, params=[], files=[]):
    data = {}
    for param in params:
        data[param] = request.POST.get(param, "")
    for file in files:
        data[file] = request.FILES.get(file, None)
    return data


def check_dictionary(dict, size=5, exclude=[]):
    for key, value in dict.items():
        if key not in exclude and len(value) < size:
            print("%s: %s" % (key, value))
            return False
    return True


def get_month_day_range(date):
    last_day = date + relativedelta(day=1, months=+1, days=-1)
    first_day = date + relativedelta(day=1)
    return first_day, last_day


def same_date(datetime1, datetime2):
    return datetime1.date() == datetime2.date()


def get_time(time_str):
    time = datetime.datetime.strptime(time_str, "%I:%M %p").time()
    return time


def parse_bootstrap_datetimepicker(time_str):
    divided = time_str.split("-")
    divided = [x.strip() for x in divided]

    if len(divided) != 2:
        return None

    datetime_format = '%m/%d/%Y %I:%M %p'

    data = None

    try:
        unaware_start_date = datetime.datetime.strptime(divided[0], datetime_format)
        unaware_end_date = datetime.datetime.strptime(divided[1], datetime_format)

        aware_start_date = pytz.utc.localize(unaware_start_date)
        aware_end_date = pytz.utc.localize(unaware_end_date)

        data = {"start": aware_start_date, "end": aware_end_date}

    except:
        print("Could not parse datetimes.")

    return data


def abstract_datetime_ranges(objects):
    data = []
    for object in objects:
        data.append({"start": object.start, "end": object.end})
    return data


def flatten_time_array(time_array):
    interval_times = []
    skip_next = False
    for i, event in enumerate(time_array):
        if not skip_next:
            interval_times.append(event["start"])
        skip_next = False

        if len(time_array) > i+1 and event["end"] > time_array[i+1]["start"]:
            skip_next = True
        else:
            interval_times.append(event["end"])

    return interval_times


def get_sun_sat(date):
    """
    :param date: A date anywhere in the week that you want
    :return: dict containing 'sun' and 'sat' of that week
    """
    idx = (date.weekday() + 1) % 7
    sun = date - datetime.timedelta(idx)
    sat = date - datetime.timedelta(idx-6)
    data = {"start": sun, "end": sat}
    print("Week: %s" % data)
    return data


def within_range_datetime(dt, start, end):
    start = pytz.utc.localize(datetime.datetime.combine(start, datetime.datetime.min.time()))
    end = pytz.utc.localize(datetime.datetime.combine(end, datetime.datetime.max.time()))
    return start <= dt <= end


def within_range_date(date, start, end):
    time = pytz.utc.localize(datetime.datetime.combine(date, datetime.datetime.min.time()))
    return start <= time <= end


def break_into_free_time(times, start, end):
    free_times = []

    if len(times) == 0:
        return [{"start": pytz.utc.localize(datetime.datetime.combine(start, datetime.datetime.min.time())),
                 "end": pytz.utc.localize(datetime.datetime.combine(end, datetime.datetime.max.time()))}]

    # Get the correct start and end of the range
    if len(times) > 0:

        # Pick to either start at start of week or end of overlapping event
        if within_range_date(start, times[0], times[1]):
            where_to_start = times[1]
            times.pop(0)
        else:
            where_to_start = pytz.utc.localize(datetime.datetime.combine(start, datetime.datetime.min.time()))
            times = [where_to_start] + times

        # Pick to either end at end of week or start of overlapping event
        if within_range_date(end, times[-2], times[-1]):
            where_to_end = times[-2]
            times.pop(len(times)-1)
        else:
            where_to_end = pytz.utc.localize(datetime.datetime.combine(end, datetime.datetime.max.time()))
            times = times + [where_to_end]

    # Remove any that don't exist outside of range
    ranges = [x for x in times if where_to_start <= x <= where_to_end]

    # Iterate over everything and get the free time blocks
    index = 1
    busy = False
    while index < len(times):
        if not busy:
            start = times[index-1]
            end = times[index]
            offset = (15 - ((15+start.minute) % 15)) if (15 - ((15+start.minute) % 15)) != 15 else 0
            data = {"start": start + datetime.timedelta(minutes=offset), "end": end}
            free_times.append(data)

        busy = not busy
        index += 1

    return free_times