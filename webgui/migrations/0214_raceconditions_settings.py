# Generated by Django 3.2.13 on 2022-06-05 16:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('webgui', '0213_auto_20220605_1059'),
    ]

    operations = [
        migrations.AddField(
            model_name='raceconditions',
            name='settings',
            field=models.TextField(blank=True, default=None, null=True),
        ),
    ]
