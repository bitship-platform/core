# Generated by Django 3.1.4 on 2020-12-10 17:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('nova_dash', '0015_app_name'),
    ]

    operations = [
        migrations.AlterField(
            model_name='app',
            name='plan',
            field=models.FloatField(choices=[(1.2, 'Base'), (2.4, 'Standard'), (4.99, 'Premium')]),
        ),
        migrations.AlterField(
            model_name='app',
            name='stack',
            field=models.URLField(choices=[('bg-success', 'Running'), ('bg-orange', 'Paused'), ('bg-info', 'Stopped'), ('bg-danger', 'Terminated')], default='Python', max_length=20),
        ),
        migrations.AlterField(
            model_name='app',
            name='status',
            field=models.CharField(choices=[('bg-success', 'Running'), ('bg-orange', 'Paused'), ('bg-info', 'Stopped'), ('bg-danger', 'Terminated')], default='STOPPED', max_length=20),
        ),
    ]