# Generated by Django 3.1.4 on 2020-12-08 04:30

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('nova_dash', '0005_auto_20201206_2005'),
    ]

    operations = [
        migrations.CreateModel(
            name='Address',
            fields=[
                ('customer', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, primary_key=True, related_name='address', serialize=False, to='nova_dash.customer')),
                ('firstname', models.CharField(max_length=50)),
                ('lastname', models.CharField(max_length=50)),
                ('location', models.TextField()),
                ('city', models.CharField(max_length=100)),
                ('country', models.CharField(max_length=100)),
                ('pincode', models.IntegerField()),
            ],
        ),
        migrations.RemoveField(
            model_name='customer',
            name='address',
        ),
        migrations.RemoveField(
            model_name='customer',
            name='pincode',
        ),
    ]
