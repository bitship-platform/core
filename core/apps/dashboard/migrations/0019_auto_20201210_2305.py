# Generated by Django 3.1.4 on 2020-12-10 17:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('nova_dash', '0018_auto_20201210_2302'),
    ]

    operations = [
        migrations.AlterField(
            model_name='app',
            name='stack',
            field=models.URLField(choices=[('https://cdn.discordapp.com/attachments/785734963458342973/786641902782251028/python.png', 'Python'), ('https://cdn.discordapp.com/attachments/785734963458342973/786647100749774908/node-js.png', 'Javascript'), ('https://cdn.discordapp.com/attachments/785734963458342973/786646064878845982/ruby.png', 'Ruby')], default='Python'),
        ),
    ]