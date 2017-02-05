import datetime
import json
import urllib

import pytz
from django.utils import timezone
from appointments.models import User, TimeOff, AppointmentType, Appointment
from django.contrib import messages
from django.contrib.auth import logout, authenticate, login
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import render, redirect
from lib.time import get_post, check_dictionary, get_time, parse_bootstrap_datetimepicker, get_month_day_range


def index(request):

    if request.method == "POST":
        json_str = request.body.decode(encoding='UTF-8')
        data = json.loads(json_str)

        name = data.get("name", "")
        email = data.get("email", "")

        if len(name) < 3 or len(email) < 3:
            return JsonResponse({"response": "error", "message": "Make sure everything is filled out."})

        if not email.endswith("@buffalo.edu"):
            return JsonResponse({"response": "error", "message": "Email must contain @buffalo.edu."})

        user_id = data.get("user_id", 0)
        user = User.objects.filter(id=int(user_id)).first()

        if not user:
            return JsonResponse({"response": "error", "message": "Could not find the user."})

        start_unaware = datetime.datetime.strptime(data["start"].replace("th", "").replace("nd", "").replace("rd", ""),
                                                   "%b %d %I:%M %p")
        start_unaware = start_unaware.replace(year=2017)
        end_unaware = datetime.datetime.strptime(data["end"].replace("th", "").replace("nd", "").replace("rd", ""),
                                                 "%b %d %I:%M %p")
        end_unaware = end_unaware.replace(year=2017)

        type_id = data["type_id"]
        type = user.appt_manager.appt_types.filter(id=int(type_id)).first()

        if not type:
            return JsonResponse({"response": "error", "message": "Could not find the type."})

        time = pytz.utc
        start = time.localize(start_unaware)
        end = time.localize(end_unaware)

        appointment = Appointment.objects.create(manager=user.appt_manager, type=type, start=start, end=end,
                                                 name=name, email=email)
        appointment.save()
        messages.success(request, "Created the appointment successfully.")
        return JsonResponse({"response": "ok"})

    try:
        user_id = int(request.GET.get("vc", 0))
    except:
        return redirect("index")

    if user_id == 0:
        user = User.objects.filter(type__contains="h__").first()
    else:
        user = User.objects.filter(type__contains="h__", id=user_id).first()

    return render(request, "dashboard/appt/index.html", {"fc_user": user,
                                                         "users": User.objects.filter(type__contains="h__", private=False).all()})


@login_required
def logout_view(request):
    logout(request)
    return redirect("index")


@login_required
def add_time_off(request):

    if request.method == "POST":
        data = get_post(request, params=["reason", "time"])
        if check_dictionary(data):
            datetimes = parse_bootstrap_datetimepicker(data["time"])

            if not datetimes:
                messages.error(request, "Please make sure the date range input is filled out correctly.")
                return redirect("manage")

            if datetimes["start"] < timezone.now():
                print(datetimes["start"])
                print(timezone.now())
                messages.error(request, "The starting time must be in the future!")
                return redirect("manage")

            time_off = TimeOff.objects.create(manager=request.user.appt_manager, reason=data["reason"],
                                              start=datetimes["start"], end=datetimes["end"])
            time_off.save()
            messages.success(request, "Successfully added the time off.")
        else:
            messages.error(request, "Please make sure everything is filled out.")

    return redirect("manage")


@login_required
def delete_time_off(request, time_id):

    time_off = request.user.appt_manager.exceptions.filter(id=int(time_id)).first()
    time_off.delete()
    messages.success(request, "Successfully removed that time off.")
    return redirect("manage")


@login_required
def save_normal_hours(request):

    if request.method == "POST":
        data = get_post(request, params=[x[0] + "_start" for x in request.user.appt_manager.DAYS] + [x[0] + "_end" for x in
                                                                                            request.user.appt_manager.DAYS])
        if not check_dictionary(data, size=4):
            messages.error(request, "Please make sure that everything is filled out correctly.")
            return redirect("manage")

        appt_manager = request.user.appt_manager
        # Run through list of days and update
        for key, value in data.items():
            time = get_time(value)
            setattr(appt_manager, key, time)
        appt_manager.save()
        messages.success(request, "Successfully updated your saved times!")

    return redirect("manage")


@login_required
def manage(request):

    time_before = timezone.now() - datetime.timedelta(weeks=2)
    for appointment in Appointment.objects.filter(end__lt=time_before):
        appointment.delete()

    if request.method == "POST":
        json_str = request.body.decode(encoding='UTF-8')
        data = json.loads(json_str)

        name = data.get("name", "")
        email = data.get("email", "")

        if len(name) < 3 or len(email) < 3:
            return JsonResponse({"response": "error", "message": "Make sure everything is filled out."})

        start_unaware = datetime.datetime.strptime(data["start"].replace("th", "").replace("nd", "").replace("rd", ""),
                                                   "%b %d %I:%M %p")
        start_unaware = start_unaware.replace(year=2017)
        end_unaware = datetime.datetime.strptime(data["end"].replace("th", "").replace("nd", "").replace("rd", ""),
                                                 "%b %d %I:%M %p")
        end_unaware = end_unaware.replace(year=2017)

        type_id = data["type_id"]
        type = request.user.appt_manager.appt_types.filter(id=int(type_id)).first()

        if not type:
            return JsonResponse({"response": "error", "message": "Could not find the type."})

        time = pytz.utc
        start = time.localize(start_unaware)
        end = time.localize(end_unaware)

        appointment = Appointment.objects.create(manager=request.user.appt_manager, type=type, start=start, end=end,
                                                 name=name, email=email)
        appointment.save()
        messages.success(request, "Created the appointment successfully.")
        return JsonResponse({"response": "ok"})

    return render(request, "dashboard/appt/manage.html")


@login_required
def create_appt_type(request):

    if request.method == "POST":
        data = get_post(request, params=["name", "minutes"])
        if check_dictionary(data, exclude=["minutes"], size=2):
            if not request.user.is_staff:  # Not staff
                appointment = AppointmentType.objects.create(name=data["name"], minutes=data["minutes"],
                                                             manager=request.user.appt_manager)
                appointment.save()
            messages.success(request, "Successfully added the new appointment type.")

        else:
            messages.error(request, "Please make sure all of the fields are filled out.")

    return redirect("manage")


@login_required
def delete_appt_type(request, type_id):

    appointment = AppointmentType.objects.filter(id=int(type_id)).first()
    if appointment:
        appointment.delete()
        messages.success(request, "Successfully deleted appointment type.")

    return redirect("manage")


@login_required
def get_todays_appt_for_user(request, user_id):

    user = User.objects.filter(id=int(user_id)).first()
    if not user:
        return JsonResponse({"response": "error", "message": "Could not find user."})

    return JsonResponse(user.appt_manager.todays_appointments, safe=False)


@login_required
def get_todays_timeoff_for_user(request, user_id):

    user = User.objects.filter(id=int(user_id)).first()
    if not user:
        return JsonResponse({"response": "error", "message": "Could not find user."})

    return JsonResponse(user.appt_manager.todays_timeoff, safe=False)


def get_available_appts(request, user_id):

    if request.method != "POST":
        return JsonResponse({"response": "error", "message": "The call must be a POST."})

    json_str = request.body.decode(encoding='UTF-8')
    data = json.loads(json_str)
    print(data)

    date = data.get("date", None)
    if not date or len(date.split("/")) != 3:
        return JsonResponse({"response": "error", "message": "Invalid 'date' argument."})
    date = date.split("/")
    date = date[2] + "-" + date[0] + "-" + date[1]

    user = User.objects.filter(type__contains="h__", id=int(user_id)).first()
    if not user:
        return JsonResponse({"response": "error", "message": "Invalid user."})

    appt_type = None

    try:
        appt_type = user.appt_manager.appt_types.filter(id=int(data["appt_id"])).first()
    except:
        pass
    if not appt_type:
        return JsonResponse({"response": "error", "message": "Invalid appointment type."})

    date_in_week = datetime.datetime.strptime(date, "%Y-%m-%d").date()

    available = user.appt_manager.get_available_in_week(date_in_week, appt_type)

    interval = 10

    if appt_type.minutes < 20:
        interval = 5
    elif appt_type.minutes > 40:
        interval = 15
    elif appt_type.minutes > 50:
        interval = 30

    return JsonResponse({"response": "ok", "date": date, "available": available, "interval": interval})


@login_required
def get_appointments_for_month(request):

    events = []
    appointments = request.user.appt_manager.appointments.all()
    exceptions = request.user.appt_manager.exceptions.all()

    for appt in appointments:
        events.append(appt.fc_serialize)
    for appt in exceptions:
        events.append(appt.fc_serialize)

    return JsonResponse(events, safe=False)


def login_view(request):

    if request.user.is_authenticated:
        return redirect("manage")

    if request.method == "POST":
        email = request.POST.get("email", "").lower()
        password = request.POST.get("password", "")

        user = authenticate(email=email, password=password)

        if user:
            login(request, user)
            return redirect("manage")

        messages.error(request, "Invalid credentials.")

    return render(request, "dashboard/session/login.html")
