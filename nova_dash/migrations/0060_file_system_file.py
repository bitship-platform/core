# Generated by Django 3.1.5 on 2021-01-20 16:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('nova_dash', '0059_customer_credits_spend'),
    ]

    operations = [
        migrations.AddField(
            model_name='file',
            name='system_file',
            field=models.BooleanField(default=False),
        ),
    ]