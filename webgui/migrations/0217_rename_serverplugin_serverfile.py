# Generated by Django 3.2.13 on 2022-06-06 07:40

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('webgui', '0216_auto_20220606_0848'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='ServerPlugin',
            new_name='ServerFile',
        ),
    ]