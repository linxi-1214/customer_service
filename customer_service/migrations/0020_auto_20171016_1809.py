# -*- coding: utf-8 -*-
# Generated by Django 1.11.3 on 2017-10-16 10:09
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('customer_service', '0019_contractresult_process'),
    ]

    operations = [
        migrations.AlterField(
            model_name='contractresult',
            name='process',
            field=models.IntegerField(default=-1, null=True),
        ),
    ]
