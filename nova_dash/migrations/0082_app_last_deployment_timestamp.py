# Generated by Django 3.1.5 on 2021-03-15 12:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('nova_dash', '0081_auto_20210313_2350'),
    ]

    operations = [
        migrations.AddField(
            model_name='app',
            name='last_deployment_timestamp',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]