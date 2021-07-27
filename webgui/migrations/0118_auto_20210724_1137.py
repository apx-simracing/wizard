# Generated by Django 3.1.4 on 2021-07-24 09:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('webgui', '0117_auto_20210702_0747'),
    ]

    operations = [
        migrations.AddField(
            model_name='server',
            name='status',
            field=models.TextField(blank=True, default=None, null=True),
        ),
        migrations.AlterField(
            model_name='server',
            name='public_secret',
            field=models.CharField(blank=True, default='dcigicgeegaadegigchh', help_text='The secret for the communication with the APX race control', max_length=500),
        ),
    ]