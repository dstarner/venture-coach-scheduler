from django.db import models
from django.contrib.auth.base_user import BaseUserManager, AbstractBaseUser
from django.db.models import Q
from django.utils import timezone
from lib.time import *


class MyUserManager(BaseUserManager):
    def create_user(self, email, first_name, last_name, password=None):
        """
        Creates and saves a User with the given email, date of
        birth and password.
        """
        if not email:
            raise ValueError('Users must have an email address')

        user = self.model(
            email=self.normalize_email(email),
            first_name=first_name,
            last_name=last_name,
        )

        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, first_name, last_name, password):
        """
        Creates and saves a superuser with the given email, date of
        birth and password.
        """
        user = self.create_user(
            email,
            password=password,
            first_name=first_name,
            last_name=last_name,
        )
        user.is_admin = True
        user.save(using=self._db)
        return user


class User(AbstractBaseUser):

    email = models.EmailField(
        verbose_name='email address',
        max_length=255,
        unique=True,
    )

    PREFIX_CHOICES = (
        ("mr", "Mr."),
        ("dr", "Dr."),
        ("ms", "Mrs."),
        ("mi", "Miss")
    )

    ACCOUNT_TYPES = (
        ("h__co", "Venture Coach"),
        ("h__sf", "Software Fellow"),
        ("h__df", "Design Fellow"),
        ("us", "User")
    )

    prefix = models.CharField(default="mr", max_length=2, help_text="Prefix for the user's name.",
                              choices=PREFIX_CHOICES)

    private = models.BooleanField(default=False)

    first_name = models.CharField(default="", max_length=128, help_text="The user's first name.")

    last_name = models.CharField(default="", max_length=128, help_text="The user's last name.")

    type = models.CharField(default="us", max_length=5, help_text="Account type.",
                            choices=ACCOUNT_TYPES)

    # If they are an active user or not.
    is_active = models.BooleanField(default=True)

    # If they are P+P admin
    is_admin = models.BooleanField(default=False)

    objects = MyUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    class Meta:
        db_table = "users"
        verbose_name_plural = "Users"
        verbose_name = "User"

    def get_full_name(self):
        # The user is identified by their email address
        return "%s %s %s" % (self.get_prefix_display(), self.first_name, self.last_name)

    def get_short_name(self):
        # The user is identified by their email address
        return "%s %s" % (self.first_name, self.last_name)

    def __str__(self):              # __unicode__ on Python 2
        return "%s : %s" % (self.get_short_name(), self.email)

    def has_perm(self, perm, obj=None):
        "Does the user have a specific permission?"
        # Simplest possible answer: Yes, always
        return True

    def has_module_perms(self, app_label):
        "Does the user have permissions to view the app `app_label`?"
        # Simplest possible answer: Yes, always
        return True

    @property
    def is_staff(self):
        "Is the user a member of staff?"
        # Simplest possible answer: All admins are staff
        return self.is_admin


class UserAppointmentManager(models.Model):

    DAYS = (
        ("sun", "Sunday"),
        ("mon", "Monday"),
        ("tue", "Tuesday"),
        ("wed", "Wednesday"),
        ("thu", "Thursday"),
        ("fri", "Friday"),
        ("sat", "Saturday"),
    )

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="appt_manager", null=True)

    sun_start = models.TimeField(default=timezone.now)
    sun_end = models.TimeField(default=timezone.now)

    mon_start = models.TimeField(default=timezone.now)
    mon_end = models.TimeField(default=timezone.now)

    tue_start = models.TimeField(default=timezone.now)
    tue_end = models.TimeField(default=timezone.now)

    wed_start = models.TimeField(default=timezone.now)
    wed_end = models.TimeField(default=timezone.now)

    thu_start = models.TimeField(default=timezone.now)
    thu_end = models.TimeField(default=timezone.now)

    fri_start = models.TimeField(default=timezone.now)
    fri_end = models.TimeField(default=timezone.now)

    sat_start = models.TimeField(default=timezone.now)
    sat_end = models.TimeField(default=timezone.now)

    class Meta:
        db_table = "user_appointment_managers"

    def __str__(self):
        return self.user.get_full_name()

    @property
    def todays_appointments(self):
        # Needs appointments and timeoff
        appointment_objs = self.appointments.filter(
            # Filter by if the start or end day is today.
            Q(start__date=timezone.now().date()) | Q(end__date=timezone.now().date())).all()
        appointment_objs = appointment_objs | self.appointments.filter(
            start__lt=timezone.now().date(), end__gt=timezone.now().date()).all()
        appts = []
        for appt in appointment_objs:
            appts.append(appt.fc_serialize)
        return appts

    @property
    def todays_timeoff(self):
        # Needs appointments and timeoff
        timeoff_objs = self.exceptions.filter(
            # Filter by if the start or end day is today.
            Q(start__date=timezone.now().date()) | Q(end__date=timezone.now().date()),
        ).all()
        # Append the ones that fall within the range
        timeoff_objs = timeoff_objs | self.exceptions.filter(
            start__lt=timezone.now().date(), end__gt=timezone.now().date()).all()
        times = []
        for time_off in timeoff_objs:
            times.append(time_off.fc_serialize)
        return times

    @property
    def get_min_time(self):
        min_time = self.sun_start
        for day in self.DAYS:
            time = getattr(self, day[0] + "_start")
            if min_time > time:
                min_time = time
        hour = int(min_time.strftime("%H")) # - 1
        return "%s:00:00" % hour

    @property
    def get_max_time(self):
        max_time = self.sun_start
        for day in self.DAYS:
            time = getattr(self, day[0] + "_end")
            if max_time < time:
                max_time = time
        hour = int(max_time.strftime("%H")) # + 1
        return "%s:00:00" % hour

    def get_appts_for_range(self, date_range):
        return self.appointments.filter(Q(start__range=date_range) | Q(end__range=date_range)).all()

    def get_time_off_for_range(self, date_range):
        return self.exceptions.filter(Q(start__range=date_range) | Q(end__range=date_range)).all()

    def get_available_in_week(self, date, appt_type):
        # Get the range for the week
        date_range = get_sun_sat(date)

        query_range = [date_range["start"], date_range["end"]]

        # Get all of the appointments for the week
        appts_this_week = self.get_appts_for_range(query_range)
        busy_time = abstract_datetime_ranges(appts_this_week)

        # Get all of the time off for the week
        times_off_this_week = self.get_time_off_for_range(query_range)
        busy_time = busy_time + abstract_datetime_ranges(times_off_this_week)
        busy_time.sort(key=lambda x:x['start'])

        # Filter through available times and accept if the total minutes is greater than the appointment type
        available_times = flatten_time_array(busy_time)

        # These are blocks of free times
        free_times = break_into_free_time(available_times, query_range[0], query_range[1])

        # Remove if block is less than time needed
        free_times = [free_time for free_time in free_times if (free_time["end"] - free_time["start"]).total_seconds() / 60 > appt_type.minutes]

        appt_times = []

        # Iterate over free blocks of time
        for block in free_times:

            cur_time = block["start"]
            cur_end = cur_time + datetime.timedelta(minutes=appt_type.minutes)

            # Break up into the blocks of time
            while cur_end <= block["end"]:

                start_day_of_week = cur_time.strftime("%a").lower()[:3]  # sun/mon/tue....
                end_day_of_week = cur_end.strftime("%a").lower()[:3]  # sun/mon/tue....

                # If within the open and close hours of the org
                if getattr(self, "%s_start" % start_day_of_week) < cur_time.time() and \
                                getattr(self, "%s_end" % end_day_of_week) > cur_end.time():
                    data = {"title": "Available", "start": cur_time.strftime("%Y/%m/%d %H:%M"),
                            "end": cur_end.strftime("%Y/%m/%d %H:%M")}
                    appt_times.append(data)

                # Update
                cur_time = cur_end
                cur_end = cur_time + datetime.timedelta(minutes=appt_type.minutes)

        return appt_times


class TimeOff(models.Model):

    manager = models.ForeignKey(UserAppointmentManager, on_delete=models.CASCADE, related_name="exceptions")

    reason = models.CharField(default="Vacation", max_length=32)

    start = models.DateTimeField(default=timezone.now)

    end = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "exceptions"
        ordering = ["start"]

    @property
    def fc_serialize(self):
        return {"title": "Time Off: %s" % self.reason, "start": self.start.strftime("%Y/%m/%d %H:%M"),
                "end": self.end.strftime("%Y/%m/%d %H:%M")}


class AppointmentType(models.Model):

    manager = models.ForeignKey(UserAppointmentManager, on_delete=models.CASCADE, related_name="appt_types")

    name = models.CharField(default="Checkup", max_length=64)

    minutes = models.IntegerField(default=45, help_text="Amount of time in minutes for the appointment.")

    class Meta:
        db_table = "appt_types"

    def __str__(self):
        return self.name


class Appointment(models.Model):

    manager = models.ForeignKey(UserAppointmentManager, on_delete=models.CASCADE, related_name="appointments")

    type = models.ForeignKey(AppointmentType, on_delete=models.CASCADE, related_name="appointments")

    name = models.CharField(default="", max_length=128)

    email = models.EmailField(default="", max_length=128)

    start = models.DateTimeField(default=timezone.now)

    end = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "appointments"
        ordering = ["start"]

    def __str__(self):
        return self.type.name + " Appointment"

    @property
    def fc_serialize(self):
        return {"title": "%s: %s" % (self.type.name, self.name), "start": self.start.strftime("%Y/%m/%d %H:%M"),
                "end": self.end.strftime("%Y/%m/%d %H:%M")}
