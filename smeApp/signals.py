from django.db.models.signals import post_delete, post_save, pre_save
from django.dispatch import receiver
from .models import PurchaseOrder, SaleItem
from django.db import transaction

@receiver(post_save, sender=PurchaseOrder)
def update_stock_on_received(sender, instance, **kwargs):
    if instance.status == PurchaseOrder.RECEIVED:
        for item in instance.purchase_order_items.all():
            stock_item = item.stock_item
            stock_item.quantity += item.quantity
            stock_item.save()

@receiver(pre_save, sender=SaleItem)
def update_stock_on_sale_pre(sender, instance, **kwargs):
    if instance.pk:
        old_instance = SaleItem.objects.get(pk=instance.pk)
        instance.old_quantity = old_instance.quantity
    else:
        instance.old_quantity = 0

@receiver(post_save, sender=SaleItem)
def update_stock_on_sale(sender, instance, created, **kwargs):
    stock_item = instance.stock_item

    if created:
        stock_item.quantity -= instance.quantity
    else:
        stock_item.quantity += instance.old_quantity
        stock_item.quantity -= instance.quantity

    with transaction.atomic():
        stock_item.save()

@receiver(post_delete, sender=SaleItem)
def update_stock_on_sale_delete(sender, instance, **kwargs):
    stock_item = instance.stock_item
    stock_item.quantity += instance.quantity
    stock_item.save()
