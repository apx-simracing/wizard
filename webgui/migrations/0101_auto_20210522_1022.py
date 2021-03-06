# Generated by Django 3.1.4 on 2021-05-22 08:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('webgui', '0100_auto_20210522_1000'),
    ]

    operations = [
        migrations.AddField(
            model_name='server',
            name='session_id',
            field=models.CharField(blank=True, default=None, help_text='APX Session Id', max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='server',
            name='public_secret',
            field=models.CharField(blank=True, default='gaccecgghaecfhfaeaab', help_text='The secret for the communication with the APX race control', max_length=500),
        ),
    ]
