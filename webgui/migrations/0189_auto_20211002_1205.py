# Generated by Django 3.1.4 on 2021-10-02 10:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('webgui', '0188_auto_20211001_1827'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='servercron',
            name='cron_text',
        ),
        migrations.RemoveField(
            model_name='servercron',
            name='last_execution',
        ),
        migrations.AddField(
            model_name='servercron',
            name='end_time',
            field=models.TimeField(blank=True, default=None, help_text='The end time the job should start', null=True),
        ),
        migrations.AddField(
            model_name='servercron',
            name='start_time',
            field=models.TimeField(blank=True, default=None, help_text='The start time the job should start', null=True),
        ),
        migrations.AddField(
            model_name='servercron',
            name='type',
            field=models.CharField(choices=[('DAILY', 'Daily'), ('MINUTE', 'Minute')], default='DAILY', help_text='On which time base should the cron job be executed?', max_length=20),
        ),
        migrations.AlterField(
            model_name='server',
            name='public_secret',
            field=models.CharField(blank=True, default='gbhbfedbfifgagiagiac', help_text='The secret for the communication with the APX race control', max_length=500),
        ),
    ]
