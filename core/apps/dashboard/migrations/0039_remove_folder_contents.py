# Generated by Django 3.1.4 on 2020-12-20 21:05

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('nova_dash', '0038_folder_contents'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='folder',
            name='contents',
        ),
    ]