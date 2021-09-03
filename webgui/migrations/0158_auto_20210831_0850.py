# Generated by Django 3.1.4 on 2021-08-31 06:50

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('webgui', '0157_auto_20210831_0845'),
    ]

    operations = [
        migrations.AddField(
            model_name='event',
            name='pit_speed_override',
            field=models.IntegerField(default=0, help_text='pitlane speed limit override in meters/sec (0=disabled)', validators=[django.core.validators.MinValueValidator(0)]),
        ),
        migrations.AlterField(
            model_name='server',
            name='public_secret',
            field=models.CharField(blank=True, default='icbdihaeecdeadggifai', help_text='The secret for the communication with the APX race control', max_length=500),
        ),
    ]