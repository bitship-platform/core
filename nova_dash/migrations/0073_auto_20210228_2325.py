# Generated by Django 3.1.5 on 2021-02-28 17:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('nova_dash', '0072_transaction'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='payer_email',
            field=models.CharField(blank=True, max_length=30, null=True),
        ),
        migrations.AlterField(
            model_name='order',
            name='payer_id',
            field=models.CharField(blank=True, max_length=20, null=True),
        ),
    ]