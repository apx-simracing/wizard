# Generated by Django 3.1.4 on 2021-08-31 06:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('webgui', '0158_auto_20210831_0850'),
    ]

    operations = [
        migrations.AddField(
            model_name='event',
            name='must_be_stopped',
            field=models.BooleanField(default=False, help_text='Whether drivers must come to a complete stop before exiting back to the monitor'),
        ),
        migrations.AlterField(
            model_name='server',
            name='public_secret',
            field=models.CharField(blank=True, default='hifdcffcihgehbechdag', help_text='The secret for the communication with the APX race control', max_length=500),
        ),
    ]
