# Generated by Django 3.1.5 on 2021-02-26 14:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('nova_dash', '0066_auto_20210226_1907'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='status',
            field=models.CharField(choices=[('text-danger', 'Failed'), ('text-warning', 'Pending'), ('text-success', 'Success')], max_length=15),
        ),
    ]
