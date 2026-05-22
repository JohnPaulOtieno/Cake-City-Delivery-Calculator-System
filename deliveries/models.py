from django.db import models
from django.contrib.auth.models import User
from stores.models import Store
from datetime import datetime


class Delivery(models.Model):
    """
    Represents a delivery order for a cake customer.
    Contains pricing, distance, and store information.
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('in_transit', 'In Transit'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    ]

    store = models.ForeignKey(Store, on_delete=models.PROTECT, related_name='deliveries')
    customer_address = models.TextField(help_text="Delivery destination address")
    customer_latitude = models.DecimalField(max_digits=9, decimal_places=6, help_text="Customer location latitude")
    customer_longitude = models.DecimalField(max_digits=9, decimal_places=6, help_text="Customer location longitude")
    customer_phone = models.CharField(max_length=20, blank=True, help_text="Customer phone number for SMS notification")
    distance_km = models.DecimalField(max_digits=8, decimal_places=2, help_text="Distance in kilometers from store to customer")
    fare_ksh = models.PositiveIntegerField(help_text="Delivery fare in Kenyan Shillings (KES)")
    
    # Manager who created the delivery
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_deliveries')
    
    # Status and timestamps
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Additional info
    notes = models.TextField(blank=True, help_text="Additional delivery notes or special instructions")

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Delivery Order"
        verbose_name_plural = "Delivery Orders"

    def __str__(self):
        return f"Delivery #{self.id} - {self.customer_address[:50]}"

    def get_coordinates(self):
        """Returns customer location tuple (latitude, longitude)"""
        return (float(self.customer_latitude), float(self.customer_longitude))

    def get_store_coordinates(self):
        """Returns store location tuple (latitude, longitude)"""
        return self.store.get_coordinates()
