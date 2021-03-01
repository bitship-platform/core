# Generated by Django 3.1.5 on 2021-03-01 05:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('nova_dash', '0073_auto_20210228_2325'),
    ]

    operations = [
        migrations.AddField(
            model_name='customer',
            name='banned',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='customer',
            name='coins',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='customer',
            name='coins_redeemed',
            field=models.IntegerField(default=0),
        ),
    ]