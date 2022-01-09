# Generated by Django 3.1.4 on 2020-12-10 17:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('nova_dash', '0013_auto_20201210_2224'),
    ]

    operations = [
        migrations.AddField(
            model_name='app',
            name='stack',
            field=models.CharField(choices=[('bg-success', 'RUNNING'), ('bg-orange', 'PAUSED'), ('bg-info', 'STOPPED'), ('bg-danger', 'TERMINATED')], default='Python', max_length=20),
        ),
    ]