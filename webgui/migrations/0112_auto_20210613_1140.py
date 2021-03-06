# Generated by Django 3.1.4 on 2021-06-13 09:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('webgui', '0111_auto_20210613_1137'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='trackupdate',
            options={'verbose_name_plural': 'Track updates'},
        ),
        migrations.RemoveField(
            model_name='trackupdate',
            name='token',
        ),
        migrations.AddField(
            model_name='trackupdate',
            name='name',
            field=models.CharField(blank=True, default=None, max_length=100, null=True, unique=True, verbose_name='An unique name do identify the track update'),
        ),
        migrations.AlterField(
            model_name='server',
            name='public_secret',
            field=models.CharField(blank=True, default='dihfidcbgbghgfebedih', help_text='The secret for the communication with the APX race control', max_length=500),
        ),
    ]
