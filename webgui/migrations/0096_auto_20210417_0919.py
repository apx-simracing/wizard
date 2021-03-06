# Generated by Django 3.1.4 on 2021-04-17 07:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('webgui', '0095_auto_20210417_0911'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='server',
            name='plugins',
        ),
        migrations.AddField(
            model_name='event',
            name='plugins',
            field=models.ManyToManyField(blank=True, to='webgui.ServerPlugin'),
        ),
        migrations.AlterField(
            model_name='server',
            name='public_secret',
            field=models.CharField(blank=True, default='adgbbchcbchadhbcahhe', help_text='The secret for the communication with the APX race control', max_length=500),
        ),
    ]
