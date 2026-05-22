from django.contrib import admin
from .models import Delivery


@admin.register(Delivery)
class DeliveryAdmin(admin.ModelAdmin):
    """Admin interface for Delivery model."""
    
    list_display = ['id', 'store', 'customer_address_short', 'distance_km', 'fare_ksh', 'status', 'created_by', 'created_at']
    list_filter = ['status', 'store', 'created_at', 'created_by']
    search_fields = ['customer_address', 'customer_phone', 'notes']
    readonly_fields = ['created_at', 'updated_at', 'created_by']
    
    fieldsets = (
        ('Store & Delivery Info', {
            'fields': ('store', 'customer_address', 'customer_phone', 'status')
        }),
        ('Location Data', {
            'fields': ('customer_latitude', 'customer_longitude'),
            'description': 'Customer coordinates in decimal format'
        }),
        ('Distance & Pricing', {
            'fields': ('distance_km', 'fare_ksh')
        }),
        ('Notes', {
            'fields': ('notes',)
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def customer_address_short(self, obj):
        """Display short version of customer address."""
        return obj.customer_address[:50] + '...' if len(obj.customer_address) > 50 else obj.customer_address
    customer_address_short.short_description = 'Address'
    
    def get_readonly_fields(self, request, obj=None):
        """Make distance and fare read-only if delivery already exists."""
        if obj:
            return self.readonly_fields + ['distance_km', 'fare_ksh']
        return self.readonly_fields
