# Generated by Django 3.2.18 on 2023-04-08 22:45

from django.db import migrations, models

def update_payment_status(apps, schema_editor):
    Job = apps.get_model('smeApp', 'Job')
    mapping = {
        'late': 'Late Payment',
    }

    for job in Job.objects.all():
        if job.payment_status in mapping:
            job.payment_status = mapping[job.payment_status]
            job.save()

class Migration(migrations.Migration):

    dependencies = [
        ('smeApp', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='job',
            name='payment_type',
            field=models.CharField(blank=True, choices=[('credit card', 'Credit Card'), ('debit card', 'Debit Card'), ('cash', 'Cash'), ('check', 'Check'), ('paypal', 'PayPal'), ('other', 'Other')], max_length=20, null=True),
        ),
    ]
