from django import template
from django.utils import timezone
from lib.time import same_date

register = template.Library()


@register.filter
def start(day):
    return day + "_start"


@register.filter
def end(day):
    return day + "_end"


@register.filter
def get_time(day, appt_manager):
    time = getattr(appt_manager, day)
    formatted = time.strftime("%I:%M %p")
    return formatted


@register.filter
def format_range(exception):
    string = ""
    if not same_date(exception.start, exception.end):
        string += exception.start.strftime("%m/%d/%Y %I:%M %p - <br/>")
        string += exception.end.strftime("%m/%d/%Y %I:%M %p")
    else:
        string += exception.start.strftime("%m/%d/%Y %I:%M %p - ")
        string += exception.end.strftime("%I:%M %p")
    return string


@register.filter
def get_dates_after_today(date_query):
    return date_query.filter(end__gte=timezone.now()).all()
