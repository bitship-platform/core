# Generated by Django 4.0.1 on 2022-10-06 21:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0007_remove_folder_owner_folder_team'),
    ]

    operations = [
        migrations.AddField(
            model_name='teamprivilege',
            name='admin',
            field=models.BooleanField(default=False),
        ),
    ]
