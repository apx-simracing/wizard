# Generated by Django 3.1.4 on 2021-08-15 08:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('webgui', '0150_auto_20210815_1014'),
    ]

    operations = [
        migrations.AddField(
            model_name='racesessions',
            name='grip_needle',
            field=models.CharField(blank=True, default=None, help_text='If you want to use the mod provided grip, add a filename/ and or part of the rrbin filename', max_length=100, null=True),
        ),
        migrations.AlterField(
            model_name='server',
            name='public_secret',
            field=models.CharField(blank=True, default='ggiagfabfgbbiiifiabi', help_text='The secret for the communication with the APX race control', max_length=500),
        ),
    ]
