# Generated by Django 3.1.4 on 2020-12-14 17:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('nova_dash', '0025_auto_20201212_1415'),
    ]

    operations = [
        migrations.AlterField(
            model_name='customer',
            name='credits',
            field=models.FloatField(default=0),
        ),
    ]