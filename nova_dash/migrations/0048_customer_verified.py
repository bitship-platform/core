# Generated by Django 3.1.4 on 2020-12-31 09:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('nova_dash', '0047_remove_customer_join_date'),
    ]

    operations = [
        migrations.AddField(
            model_name='customer',
            name='verified',
            field=models.BooleanField(default=False),
        ),
    ]