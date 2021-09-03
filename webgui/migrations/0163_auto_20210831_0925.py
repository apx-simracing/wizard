# Generated by Django 3.1.4 on 2021-08-31 07:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('webgui', '0162_auto_20210831_0909'),
    ]

    operations = [
        migrations.AddField(
            model_name='event',
            name='colission_fade_threshold',
            field=models.FloatField(default=0.7, help_text='Collision impacts are reduced to zero at this latency'),
        ),
        migrations.AlterField(
            model_name='server',
            name='public_secret',
            field=models.CharField(blank=True, default='ghihbefeecehdbdgdhee', help_text='The secret for the communication with the APX race control', max_length=500),
        ),
    ]