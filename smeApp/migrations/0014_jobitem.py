# Generated by Django 3.2.18 on 2023-04-28 05:56

import django.core.validators
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('smeApp', '0013_alter_customuser_company'),
    ]

    operations = [
        migrations.CreateModel(
            name='JobItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('item_name', models.CharField(help_text='Enter the name of the item or service.', max_length=100, verbose_name='Item Name')),
                ('item_description', models.CharField(blank=True, help_text='Enter a brief description of the item or service.', max_length=255, null=True, verbose_name='Item Description')),
                ('quantity', models.IntegerField(help_text='Enter the quantity of the item or service.', validators=[django.core.validators.MinValueValidator(1)], verbose_name='Quantity')),
                ('unit_price', models.DecimalField(decimal_places=2, help_text='Enter the unit price of the item or service.', max_digits=10, validators=[django.core.validators.MinValueValidator(0)], verbose_name='Unit Price')),
                ('job', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='smeApp.job')),
            ],
        ),
    ]