"""venture_schedule URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.10/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url
from django.contrib import admin
from appointments.views import *

urlpatterns = [
    url(r'^$', index, name="index"),
    url(r'^manage$', manage, name="manage"),
    url(r'^hours/save$', save_normal_hours, name="save_hours"),
    url(r'^type/create$', create_appt_type, name="create_type"),
    url(r'^time/create$', add_time_off, name="create_timeoff"),
    url(r'^session$', login_view, name="login_view"),
    url(r'^time/month$', get_appointments_for_month, name="get_month"),
    url(r'^load/appts/(?P<user_id>[-\d]+)$', get_available_appts, name="get_appts"),
    url(r'^time/(?P<user_id>[-\d]+)/today$', get_todays_timeoff_for_user, name="get_today_timeoff"),
    url(r'^(?P<user_id>[-\d]+)/today$', get_todays_appt_for_user, name="get_today_appt"),
    url(r'^time/(?P<time_id>[-\d]+)/delete$', delete_time_off, name="delete_timeoff"),
    url(r'^type/(?P<type_id>[-\d]+)/delete$', delete_appt_type, name="delete_type"),
    url(r'^logout$', logout_view, name="logout_view"),
    url(r'^admin/', admin.site.urls),
]
