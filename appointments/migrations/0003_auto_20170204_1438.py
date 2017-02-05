# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-02-04 19:38
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('appointments', '0002_user_private'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='prefix',
            field=models.CharField(choices=[('mr', 'Mr.'), ('dr', 'Dr.'), ('ms', 'Mrs.'), ('mi', 'Miss')], default='mr', help_text="Prefix for the user's name.", max_length=2),
        ),
    ]