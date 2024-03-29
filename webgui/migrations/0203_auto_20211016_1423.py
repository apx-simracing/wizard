# Generated by Django 3.1.4 on 2021-10-16 12:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('webgui', '0202_auto_20211011_0837'),
    ]

    operations = [
        migrations.AddField(
            model_name='event',
            name='weather_api',
            field=models.CharField(blank=True, choices=[('OpenWeatherMap', 'OpenWeatherMap'), ('DarkSky', 'DarkSky'), ('ClimaCell', 'ClimaCell'), ('ClimaCell_V4', 'ClimaCell_V4')], default=None, help_text='The Weather API to use', max_length=20, null=True, verbose_name='Weather API'),
        ),
        migrations.AddField(
            model_name='event',
            name='weather_key',
            field=models.CharField(blank=True, default=None, help_text='The key to use for the weather API.', max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='server',
            name='public_secret',
            field=models.CharField(blank=True, default='klkbchalmegguxsiejjf', help_text='The secret for the communication with the APX race control', max_length=500),
        ),
    ]
