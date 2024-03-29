# Generated by Django 3.1.4 on 2021-10-09 08:45

from django.db import migrations, models
import webgui.storage
import webgui.util


class Migration(migrations.Migration):

    dependencies = [
        ('webgui', '0199_auto_20211009_0939'),
    ]

    operations = [
        migrations.AddField(
            model_name='component',
            name='component_files',
            field=models.FileField(blank=True, null=True, storage=webgui.storage.OverwriteStorage, upload_to=webgui.util.get_update_filename),
        ),
        migrations.AlterField(
            model_name='server',
            name='public_secret',
            field=models.CharField(blank=True, default='hdbahbiifghfbfdbbcib', help_text='The secret for the communication with the APX race control', max_length=500),
        ),
    ]
