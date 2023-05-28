# Generated by Django 3.2.18 on 2023-05-28 00:43

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('smeApp', '0019_auto_20230514_1608'),
    ]

    operations = [
        migrations.AlterField(
            model_name='invoice',
            name='job',
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='invoices', to='smeApp.job'),
        ),
    ]