# Generated by Django 3.1.4 on 2021-03-06 09:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('webgui', '0064_auto_20210228_1131'),
    ]

    operations = [
        migrations.AddField(
            model_name='server',
            name='public_secret',
            field=models.CharField(blank=True, default='cffhddcfgahchafbhifg', help_text='The secret for the communication with the APX race control', max_length=500),
        ),
    ]
