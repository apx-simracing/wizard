# Generated by Django 3.1.4 on 2021-01-08 18:24

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('webgui', '0010_auto_20210108_1919'),
    ]

    operations = [
        migrations.AddField(
            model_name='server',
            name='event',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, to='webgui.event'),
        ),
    ]
