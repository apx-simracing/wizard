# Generated by Django 3.1.4 on 2021-02-06 09:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('webgui', '0036_auto_20210206_1035'),
    ]

    operations = [
        migrations.AlterField(
            model_name='component',
            name='template',
            field=models.TextField(blank=True, default='', null=True),
        ),
    ]
