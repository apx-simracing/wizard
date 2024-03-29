# Generated by Django 3.1.4 on 2021-08-31 09:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('webgui', '0169_auto_20210831_1129'),
    ]

    operations = [
        migrations.AddField(
            model_name='event',
            name='enable_auto_downloads',
            field=models.BooleanField(default=True, help_text='Whether to allow clients to autodownload files that they are missing.'),
        ),
        migrations.AlterField(
            model_name='server',
            name='public_secret',
            field=models.CharField(blank=True, default='cbcdhhaacfcfccdfchgb', help_text='The secret for the communication with the APX race control', max_length=500),
        ),
    ]
