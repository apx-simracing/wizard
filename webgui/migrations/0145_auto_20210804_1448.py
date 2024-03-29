# Generated by Django 3.1.4 on 2021-08-04 12:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('webgui', '0144_auto_20210804_0952'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='component',
            name='component_version',
        ),
        migrations.AlterField(
            model_name='component',
            name='is_official',
            field=models.BooleanField(default=False, help_text="Is official content which follows the even version and uneven version scheme (APX will select versions for you). If not checked, we will use the version you've selected."),
        ),
        migrations.AlterField(
            model_name='server',
            name='public_secret',
            field=models.CharField(blank=True, default='dedcgchihchfffaibahf', help_text='The secret for the communication with the APX race control', max_length=500),
        ),
    ]
