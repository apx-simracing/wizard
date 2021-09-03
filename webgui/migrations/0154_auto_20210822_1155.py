# Generated by Django 3.1.4 on 2021-08-22 09:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('webgui', '0153_auto_20210822_1154'),
    ]

    operations = [
        migrations.AddField(
            model_name='servercron',
            name='apply_only_if_practice',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='server',
            name='public_secret',
            field=models.CharField(blank=True, default='iccicbaeceaaeefgcaed', help_text='The secret for the communication with the APX race control', max_length=500),
        ),
    ]