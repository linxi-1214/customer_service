# -*- coding: utf-8 -*-
# Generated by Django 1.11.3 on 2017-09-28 10:07
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('customer_service', '0010_playerimport_stored_name'),
    ]

    operations = [
        migrations.CreateModel(
            name='PlayerLoginInfo',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('login_time', models.DateTimeField(null=True)),
                ('game', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='customer_service.Game')),
            ],
            options={
                'db_table': 'player_login_info',
            },
        ),
        migrations.AddField(
            model_name='player',
            name='come_from',
            field=models.CharField(max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='playerlogininfo',
            name='player',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='customer_service.Player'),
        ),
    ]
