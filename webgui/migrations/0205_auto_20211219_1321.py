# Generated by Django 3.1.4 on 2021-12-19 12:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('webgui', '0204_auto_20211031_1218'),
    ]

    operations = [
        migrations.AddField(
            model_name='server',
            name='ignore_start_hook',
            field=models.BooleanField(default=True, help_text="Don't fire the Discord messages when the server starts"),
        ),
        migrations.AddField(
            model_name='server',
            name='ignore_stop_hook',
            field=models.BooleanField(default=True, help_text="Don't fire the Discord messages when the server stops"),
        ),
        migrations.AddField(
            model_name='server',
            name='ignore_updates_hook',
            field=models.BooleanField(default=True, help_text="Don't fire the Discord messages when the server stops"),
        ),
        migrations.AlterField(
            model_name='event',
            name='force_versions',
            field=models.CharField(choices=[('0', 'Use the versions as user provided: If more than 1 version, use latest even version if updates are needed and the latest if not.'), ('1', 'Try to guess versions: If base mod is encrypted, use this version for updates, else use the latest version.'), ('2', 'Same as second option, but use the scheme also for mods without an encrypted base mod')], default='0', help_text='Versioning scheme', max_length=10),
        ),
        migrations.AlterField(
            model_name='server',
            name='action',
            field=models.CharField(blank=True, choices=[('S+', 'Start'), ('R-', 'Stop'), ('D', 'Update config and redeploy'), ('D+F', 'Update config and redeploy, force content re-installation'), ('U', 'Update to latest version of Steam branch'), ('W', 'Restart weekend')], default='', help_text='Runs an activity on the server.', max_length=3, verbose_name='Pending action to submit'),
        ),
        migrations.AlterField(
            model_name='server',
            name='public_secret',
            field=models.CharField(blank=True, default='opwxsrbhqgtdvkklismn', help_text='The secret for the communication with the APX race control', max_length=500),
        ),
        migrations.AlterField(
            model_name='servercron',
            name='action',
            field=models.CharField(blank=True, choices=[('S+', 'Start'), ('R-', 'Stop'), ('D', 'Update config and redeploy'), ('D+F', 'Update config and redeploy, force content re-installation'), ('U', 'Update to latest version of Steam branch'), ('W', 'Restart weekend')], default='', help_text='Runs an activity on the server.', max_length=3, verbose_name='Pending action to submit'),
        ),
    ]
