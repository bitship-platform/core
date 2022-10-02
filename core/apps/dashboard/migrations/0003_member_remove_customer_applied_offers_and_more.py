# Generated by Django 4.0.1 on 2022-10-02 08:39

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('dashboard', '0002_remove_customer_affiliate_commission_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='Member',
            fields=[
                ('id', models.BigIntegerField(primary_key=True, serialize=False)),
                ('tag', models.CharField(default='0000', max_length=5)),
                ('avatar', models.CharField(max_length=50, null=True)),
                ('verified', models.BooleanField(default=False)),
                ('banned', models.BooleanField(default=False)),
                ('creation_date', models.DateTimeField(blank=True, null=True)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='customer', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.RemoveField(
            model_name='customer',
            name='applied_offers',
        ),
        migrations.RemoveField(
            model_name='customer',
            name='user',
        ),
        migrations.RemoveField(
            model_name='promo',
            name='offer',
        ),
        migrations.RemoveField(
            model_name='referral',
            name='affiliate',
        ),
        migrations.RemoveField(
            model_name='setting',
            name='new_offers_alert',
        ),
        migrations.DeleteModel(
            name='Address',
        ),
        migrations.DeleteModel(
            name='Offer',
        ),
        migrations.DeleteModel(
            name='Promo',
        ),
        migrations.DeleteModel(
            name='Referral',
        ),
        migrations.AlterField(
            model_name='app',
            name='owner',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='dashboard.member'),
        ),
        migrations.AlterField(
            model_name='folder',
            name='owner',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='dashboard.member'),
        ),
        migrations.AlterField(
            model_name='order',
            name='customer',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='order', to='dashboard.member'),
        ),
        migrations.AlterField(
            model_name='setting',
            name='customer',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, primary_key=True, related_name='settings', serialize=False, to='dashboard.member'),
        ),
        migrations.DeleteModel(
            name='Customer',
        ),
    ]