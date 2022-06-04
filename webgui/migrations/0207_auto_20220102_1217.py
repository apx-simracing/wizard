# Generated by Django 3.1.4 on 2022-01-02 11:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('webgui', '0206_auto_20220102_1139'),
    ]

    operations = [
        migrations.AddField(
            model_name='timetable',
            name='current_event_time',
            field=models.IntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='server',
            name='public_secret',
            field=models.CharField(blank=True, default='eiaqyjkpjqjqqavyfsmk', help_text='The secret for the communication with the APX race control', max_length=500),
        ),
    ]