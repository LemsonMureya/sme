# Generated by Django 3.1.7 on 2023-03-29 18:34

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('smeApp', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='customuser',
            name='date_joined',
        ),
    ]