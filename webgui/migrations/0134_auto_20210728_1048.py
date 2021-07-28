# Generated by Django 3.1.4 on 2021-07-28 08:48

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('webgui', '0133_auto_20210728_1023'),
    ]

    operations = [
        migrations.AddField(
            model_name='event',
            name='failures',
            field=models.CharField(choices=[('0', 'None'), ('1', 'Normal'), ('2', 'Timescaled')], default='0', help_text='Mechanical failure rates', max_length=50),
        ),
        migrations.AddField(
            model_name='event',
            name='fuel_multiplier',
            field=models.IntegerField(default=0, help_text='Fuel usage multiplier, use 0 to disable completely', validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(7)]),
        ),
        migrations.AddField(
            model_name='event',
            name='rules',
            field=models.CharField(choices=[('0', 'None'), ('1', 'Penalties only'), ('2', 'Penalties & full-course yellows'), ('3', 'Everything except DQs')], default='0', help_text='Race rules', max_length=50),
        ),
        migrations.AddField(
            model_name='event',
            name='tire_multiplier',
            field=models.IntegerField(default=0, help_text='Tire usage multiplier, use 0 to disable completely', validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(7)]),
        ),
        migrations.AlterField(
            model_name='server',
            name='public_secret',
            field=models.CharField(blank=True, default='bhfaadbeiadihagdafha', help_text='The secret for the communication with the APX race control', max_length=500),
        ),
    ]