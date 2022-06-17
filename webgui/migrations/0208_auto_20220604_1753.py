# Generated by Django 3.2.13 on 2022-06-04 15:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('webgui', '0207_auto_20220102_1217'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='tickermessage',
            name='server',
        ),
        migrations.RemoveField(
            model_name='timetable',
            name='server',
        ),
        migrations.AlterField(
            model_name='server',
            name='public_secret',
            field=models.CharField(blank=True, default='poqtimsxqkuzwerluzuo', help_text='The secret for the communication with the APX race control', max_length=500),
        ),
        migrations.DeleteModel(
            name='Participant',
        ),
        migrations.DeleteModel(
            name='TickerMessage',
        ),
        migrations.DeleteModel(
            name='Timetable',
        ),
    ]
