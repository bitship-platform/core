# Generated by Django 3.1.4 on 2020-12-20 20:11

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('nova_dash', '0029_file_folder'),
    ]

    operations = [
        migrations.AddField(
            model_name='folder',
            name='folder',
            field=models.OneToOneField(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='master', to='nova_dash.folder'),
        ),
    ]