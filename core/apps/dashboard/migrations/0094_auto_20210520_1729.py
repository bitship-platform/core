# Generated by Django 3.2 on 2021-05-20 17:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('nova_dash', '0093_customer_dark_mode'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='customer',
            name='dark_mode',
        ),
        migrations.AddField(
            model_name='setting',
            name='auto_dark_mode',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='setting',
            name='dark_mode',
            field=models.BooleanField(default=False),
        ),
    ]