# Generated by Django 3.1.4 on 2021-04-17 06:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('webgui', '0091_auto_20210417_0844'),
    ]

    operations = [
        migrations.AlterField(
            model_name='server',
            name='public_secret',
            field=models.CharField(blank=True, default='cabhdbhidcfifiigahdi', help_text='The secret for the communication with the APX race control', max_length=500),
        ),
    ]
