# Generated by Django 3.1.4 on 2021-03-28 09:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('webgui', '0077_auto_20210328_1057'),
    ]

    operations = [
        migrations.AddField(
            model_name='entry',
            name='pit_group',
            field=models.IntegerField(default=1, help_text='The pit group for the entry. Stock tracks commonly using groups 1-30.'),
        ),
        migrations.AlterField(
            model_name='server',
            name='public_secret',
            field=models.CharField(blank=True, default='ghcaffdegdiedaaibaha', help_text='The secret for the communication with the APX race control', max_length=500),
        ),
    ]
