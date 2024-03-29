# Generated by Django 3.1.4 on 2021-09-11 08:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('webgui', '0177_auto_20210904_1645'),
    ]

    operations = [
        migrations.AddField(
            model_name='event',
            name='skip_all_session_unless_configured',
            field=models.BooleanField(default=False, help_text='Instead of using default values from the player.JSON/ multiplayer.JSON, skip all sessions unless the ones configured within APX.'),
        ),
        migrations.AlterField(
            model_name='component',
            name='component_name',
            field=models.CharField(default='Example_Mod', max_length=200),
        ),
        migrations.AlterField(
            model_name='event',
            name='welcome_message',
            field=models.TextField(blank=True, default=None, help_text='Welcome message. You can insert the driver name with the placeholder {driver_name}', null=True),
        ),
        migrations.AlterField(
            model_name='server',
            name='public_secret',
            field=models.CharField(blank=True, default='hfccgiffiiccabfebbhc', help_text='The secret for the communication with the APX race control', max_length=500),
        ),
    ]
