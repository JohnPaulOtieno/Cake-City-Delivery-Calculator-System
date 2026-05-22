from django.db import models


class Store(models.Model):
    """
    Represents a cake delivery store location.
    Stores contain latitude/longitude coordinates for Nairobi locations.
    """
    name = models.CharField(max_length=255, unique=True, help_text="Store name (e.g., 'Westlands Branch')")
    latitude = models.DecimalField(max_digits=9, decimal_places=6, help_text="Geographic latitude")
    longitude = models.DecimalField(max_digits=9, decimal_places=6, help_text="Geographic longitude")
    address = models.TextField(help_text="Full physical address of the store")
    phone_number = models.CharField(max_length=20, blank=True, help_text="Store contact number")
    is_active = models.BooleanField(default=True, help_text="Whether this store is currently operational")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        verbose_name = "Store Location"
        verbose_name_plural = "Store Locations"

    def __str__(self):
        return f"{self.name} ({self.address})"

    def get_coordinates(self):
        """Returns a tuple of (latitude, longitude)"""
        return (float(self.latitude), float(self.longitude))
