# Generated by Django 3.1.4 on 2021-10-02 12:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('webgui', '0190_auto_20211002_1208'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='servercron',
            name='type',
        ),
        migrations.AlterField(
            model_name='server',
            name='public_secret',
            field=models.CharField(blank=True, default='gdicahaadcbhceacadhi', help_text='The secret for the communication with the APX race control', max_length=500),
        ),
    ]
