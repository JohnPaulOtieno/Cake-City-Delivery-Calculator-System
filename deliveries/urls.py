from django.urls import path
from . import views

urlpatterns = [
    # New delivery
    path('new/', views.new_delivery_view, name='new_delivery'),
    
    # AJAX endpoints
    path('api/fare-preview/', views.fare_preview_ajax, name='fare_preview'),
    path('api/address-autocomplete/', views.address_autocomplete, name='address_autocomplete'),
    
    # Order history and management
    path('history/', views.order_history_view, name='order_history'),
    path('receipt/<int:pk>/', views.delivery_receipt_view, name='delivery_receipt'),
    
    # Analytics
    path('dashboard/', views.analytics_dashboard_view, name='analytics_dashboard'),
]
