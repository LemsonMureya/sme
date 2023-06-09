# Generated by Django 3.2.18 on 2023-04-19 05:52

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('smeApp', '0010_auto_20230418_1719'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='purchaseorderitem',
            name='total_purchase_price',
        ),
        migrations.RemoveField(
            model_name='stockitem',
            name='type',
        ),
        migrations.AlterField(
            model_name='purchaseorderitem',
            name='expense',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='smeApp.expense'),
        ),
        migrations.AlterField(
            model_name='saleitem',
            name='expense',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='smeApp.expense'),
        ),
        migrations.CreateModel(
            name='ProductType',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, verbose_name='Type Name')),
                ('company', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='product_types', to='smeApp.companyprofile')),
            ],
        ),
        migrations.AddField(
            model_name='stockitem',
            name='product_type',
            field=models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='stock_items', to='smeApp.producttype', verbose_name='Product Type'),
        ),
    ]
