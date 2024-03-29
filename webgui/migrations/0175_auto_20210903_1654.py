# Generated by Django 3.1.4 on 2021-09-03 14:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('webgui', '0174_auto_20210903_1644'),
    ]

    operations = [
        migrations.AddField(
            model_name='event',
            name='deny_votings',
            field=models.BooleanField(default=False, help_text='Deny all admin functionalities for non-admins'),
        ),
        migrations.AlterField(
            model_name='server',
            name='public_secret',
            field=models.CharField(blank=True, default='gdhfbgaiegacidccfedd', help_text='The secret for the communication with the APX race control', max_length=500),
        ),
    ]
