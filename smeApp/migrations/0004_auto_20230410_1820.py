# Generated by Django 3.2.18 on 2023-04-10 22:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('smeApp', '0003_auto_20230408_1908'),
    ]

    operations = [
        migrations.AddField(
            model_name='invoice',
            name='discount',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=10),
        ),
        migrations.AddField(
            model_name='invoice',
            name='tax',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=5),
        ),
    ]
