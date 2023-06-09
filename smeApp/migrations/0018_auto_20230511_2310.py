# Generated by Django 3.2.18 on 2023-05-12 03:10

from django.db import migrations

def update_num_employees(apps, schema_editor):
    CompanyProfile = apps.get_model('smeApp', 'CompanyProfile')

    mapping = {
        '1': 'solo',
        '2_to_10': 'small',
        '11_to_50': 'medium',
        '51_to_200': 'large',
        '200_plus': 'extra',
    }

    for profile in CompanyProfile.objects.all():
        profile.num_employees = mapping.get(profile.num_employees, 'solo')
        profile.save()

class Migration(migrations.Migration):

    dependencies = [
        ('smeApp', '0017_auto_20230511_2207'),
    ]

    operations = [
    ]
