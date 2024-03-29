# Generated by Django 3.1.4 on 2021-09-19 10:03

import django.core.validators
from django.db import migrations, models
import webgui.storage
import webgui.util


class Migration(migrations.Migration):

    dependencies = [
        ('webgui', '0182_auto_20210918_1031'),
    ]

    operations = [
        migrations.AddField(
            model_name='entry',
            name='base_class',
            field=models.CharField(default='Example Team', max_length=200),
        ),
        migrations.AlterField(
            model_name='component',
            name='component_name',
            field=models.CharField(default='Example_Mod', help_text='This is the folder name inside Installed/Vehicles/ or Installed/Locations/', max_length=200),
        ),
        migrations.AlterField(
            model_name='component',
            name='short_name',
            field=models.CharField(default=webgui.util.get_random_short_name, help_text="The short name is required to idenitfy (livery) filenames belonging to this component. You only need this when 'Do update' is checked.", max_length=200, validators=[django.core.validators.RegexValidator('^[0-9a-zA-Z_-]*$', 'Only alphanumeric characters and dashes are allowed.')]),
        ),
        migrations.AlterField(
            model_name='event',
            name='forced_driving_view',
            field=models.CharField(choices=[('0', 'no restrictions on driving view'), ('1', 'cockpit/tv cockpit/nosecam only'), ('3', 'cockpit only'), ('4', 'tracksides'), ('5', 'tracksides group 1')], default='0', help_text='Enforce a certain view for clients', max_length=50),
        ),
        migrations.AlterField(
            model_name='event',
            name='signup_components',
            field=models.ManyToManyField(help_text='Cars allowed to be used. If no entries are existing, all available entries from the mod will be used.', to='webgui.Component', verbose_name='Cars'),
        ),
        migrations.AlterField(
            model_name='raceconditions',
            name='rfm',
            field=models.FileField(blank=True, default=None, help_text='An rFm file to overwrite standards, speeds, pit boxes etc.', null=True, storage=webgui.storage.OverwriteStorage, upload_to=webgui.util.get_conditions_file_root, verbose_name='Alternative rFm file'),
        ),
        migrations.AlterField(
            model_name='server',
            name='public_secret',
            field=models.CharField(blank=True, default='hhagbhibcdfgebgeiaaa', help_text='The secret for the communication with the APX race control', max_length=500),
        ),
    ]
