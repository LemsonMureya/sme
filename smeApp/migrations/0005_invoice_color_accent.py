# Generated by Django 3.2.18 on 2023-04-11 16:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('smeApp', '0004_auto_20230410_1820'),
    ]

    operations = [
        migrations.AddField(
            model_name='invoice',
            name='color_accent',
            field=models.CharField(default='#0097eb', max_length=7),
        ),
    ]