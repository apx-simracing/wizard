# Generated by Django 3.1.4 on 2021-01-03 15:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('webgui', '0005_raceconditions_description'),
    ]

    operations = [
        migrations.AddField(
            model_name='server',
            name='tracks',
            field=models.ManyToManyField(to='webgui.Track'),
        ),
    ]
