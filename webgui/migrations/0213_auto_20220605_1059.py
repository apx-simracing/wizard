# Generated by Django 3.2.13 on 2022-06-05 08:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('webgui', '0212_auto_20220605_1049'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='server',
            name='public_secret',
        ),
        migrations.AddField(
            model_name='server',
            name='local_path',
            field=models.CharField(blank=True, help_text='The path where an APX created server is located inside server_children', max_length=255),
        ),
        migrations.DeleteModel(
            name='Chat',
        ),
    ]