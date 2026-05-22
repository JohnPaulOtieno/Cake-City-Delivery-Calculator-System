from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView, LogoutView
from django.db.models import Q, Count, Sum, Avg, F
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
import json

from .models import Delivery
from .forms import DeliveryForm, OrderHistoryFilterForm
from stores.models import Store
from .utils import (
    calculate_fare,
    find_nearest_store,
    get_delivery_details
)


# ============================================================================
# Authentication Views
# ============================================================================

class CustomLoginView(LoginView):
    """Custom login view for managers."""
    template_name = 'deliveries/login.html'
    redirect_authenticated_user = True


# ============================================================================
# Core Delivery Views
# ============================================================================

@login_required
@require_http_methods(["GET", "POST"])
def new_delivery_view(request):
    """
    Main view for creating a new delivery order.
    
    GET: Display form with map
    POST: Save delivery to database
    """
    if request.method == 'POST':
        form = DeliveryForm(request.POST)
        if form.is_valid():
            delivery = form.save(commit=False)
            delivery.created_by = request.user
            delivery.save()
            
            # Redirect to receipt
            return redirect('delivery_receipt', pk=delivery.id)
    else:
        form = DeliveryForm()
    
    context = {
        'form': form,
        'page_title': 'New Delivery Order',
        'stores': Store.objects.filter(is_active=True),
    }
    
    return render(request, 'deliveries/new_delivery.html', context)


@login_required
@require_http_methods(["POST"])
def fare_preview_ajax(request):
    """
    AJAX endpoint for live fare preview.
    
    Takes customer address and optional store_id.
    Returns JSON with:
    - nearest_store_id
    - nearest_store_name
    - store_lat, store_lng
    - distance_km
    - fare_ksh
    - customer_lat, customer_lng
    - decoded_address
    """
    try:
        data = json.loads(request.body)
        customer_address = data.get('customer_address', '').strip()
        store_id = data.get('store_id')
        
        if not customer_address:
            return JsonResponse({'error': 'Address is required'}, status=400)
        
        # Determine which store to use
        if store_id:
            # User selected a specific store
            store = get_object_or_404(Store, id=store_id, is_active=True)
        else:
            # Find nearest store
            store = Store.objects.filter(is_active=True).first()
            if not store:
                return JsonResponse({'error': 'No active stores available'}, status=400)
        
        # Get delivery details (distance & fare)
        delivery_details = get_delivery_details(
            float(store.latitude),
            float(store.longitude),
            customer_address
        )
        
        if delivery_details['fare'] is None:
            return JsonResponse({
                'error': 'Could not calculate distance. Please verify the address.'
            }, status=400)
        
        return JsonResponse({
            'success': True,
            'nearest_store_id': store.id,
            'nearest_store_name': store.name,
            'store_lat': float(store.latitude),
            'store_lng': float(store.longitude),
            'distance_km': delivery_details['distance_km'],
            'fare_ksh': delivery_details['fare'],
            'customer_lat': delivery_details['customer_lat'],
            'customer_lng': delivery_details['customer_lng'],
            'decoded_address': delivery_details['decoded_address'],
            'method': delivery_details['method']
        })
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


# ============================================================================
# Order History & Management
# ============================================================================

@login_required
@require_http_methods(["GET"])
def order_history_view(request):
    """
    Display order history with filtering capabilities.
    """
    # Get all deliveries for the manager
    deliveries = Delivery.objects.filter(created_by=request.user).select_related('store')
    
    # Handle filters
    filter_form = OrderHistoryFilterForm(request.GET)
    
    if filter_form.is_valid():
        # Date filter
        date_range = filter_form.cleaned_data.get('date_range')
        now = timezone.now()
        
        if date_range == 'today':
            start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
            deliveries = deliveries.filter(created_at__gte=start_date)
        elif date_range == 'week':
            start_date = now - timedelta(days=7)
            deliveries = deliveries.filter(created_at__gte=start_date)
        elif date_range == 'month':
            start_date = now - timedelta(days=30)
            deliveries = deliveries.filter(created_at__gte=start_date)
        elif date_range == 'custom':
            date_from = filter_form.cleaned_data.get('date_from')
            date_to = filter_form.cleaned_data.get('date_to')
            if date_from:
                deliveries = deliveries.filter(created_at__date__gte=date_from)
            if date_to:
                deliveries = deliveries.filter(created_at__date__lte=date_to)
        
        # Store filter
        store_id = filter_form.cleaned_data.get('store')
        if store_id:
            deliveries = deliveries.filter(store_id=store_id)
        
        # Status filter
        status = filter_form.cleaned_data.get('status')
        if status:
            deliveries = deliveries.filter(status=status)
    
    # Pagination
    page = request.GET.get('page', 1)
    per_page = 25
    total = deliveries.count()
    start_idx = (int(page) - 1) * per_page
    end_idx = start_idx + per_page
    
    page_deliveries = deliveries[start_idx:end_idx]
    total_pages = (total + per_page - 1) // per_page
    
    # Summary stats
    stats = {
        'total': total,
        'total_revenue': deliveries.aggregate(Sum('fare_ksh'))['fare_ksh__sum'] or 0,
        'avg_distance': deliveries.aggregate(Avg('distance_km'))['distance_km__avg'] or 0,
        'avg_fare': deliveries.aggregate(Avg('fare_ksh'))['fare_ksh__avg'] or 0,
    }
    
    context = {
        'page_title': 'Delivery History',
        'deliveries': page_deliveries,
        'filter_form': filter_form,
        'stats': stats,
        'current_page': int(page),
        'total_pages': total_pages,
    }
    
    return render(request, 'deliveries/order_history.html', context)


@login_required
@require_http_methods(["GET"])
def delivery_receipt_view(request, pk):
    """
    Display receipt for a specific delivery.
    """
    delivery = get_object_or_404(Delivery, id=pk, created_by=request.user)
    
    context = {
        'page_title': f'Delivery Receipt #{delivery.id}',
        'delivery': delivery,
    }
    
    return render(request, 'deliveries/receipt.html', context)


# ============================================================================
# Analytics & Dashboard
# ============================================================================

@login_required
@require_http_methods(["GET"])
def analytics_dashboard_view(request):
    """
    Display analytics dashboard with charts and insights.
    """
    # Calculate date range (default: last 30 days)
    days = int(request.GET.get('days', 30))
    start_date = timezone.now() - timedelta(days=days)
    
    # Get deliveries in range
    deliveries = Delivery.objects.filter(
        created_by=request.user,
        created_at__gte=start_date
    ).select_related('store')
    
    # Overall statistics
    total_deliveries = deliveries.count()
    total_revenue = deliveries.aggregate(Sum('fare_ksh'))['fare_ksh__sum'] or 0
    avg_distance = deliveries.aggregate(Avg('distance_km'))['distance_km__avg'] or 0
    avg_fare = deliveries.aggregate(Avg('fare_ksh'))['fare_ksh__avg'] or 0
    
    # Deliveries by store
    deliveries_by_store = deliveries.values('store__name').annotate(
        count=Count('id'),
        total_revenue=Sum('fare_ksh'),
        avg_distance=Avg('distance_km')
    ).order_by('-count')
    
    # Deliveries by hour (for peak hours chart)
    deliveries_by_hour =[]
    for hour in range(24):
        count = deliveries.filter(created_at__hour=hour).count()
        deliveries_by_hour.append({
            'hour': f'{hour:02d}:00', 
            'count': count,
            'height_percentage': count * 10
        })
    
    # Deliveries by status
    deliveries_by_status = deliveries.values('status').annotate(count=Count('id'))
    
    # Heatmap data (all deliveries for map visualization)
    heatmap_data = []
    for delivery in deliveries:
        if delivery.customer_latitude and delivery.customer_longitude:
            heatmap_data.append({
                'lat': float(delivery.customer_latitude),
                'lng': float(delivery.customer_longitude),
                'intensity': 1
            })
    
    context = {
        'page_title': 'Analytics Dashboard',
        'total_deliveries': total_deliveries,
        'total_revenue': f"{total_revenue:,} KES",
        'avg_distance': f"{avg_distance:.2f} km",
        'avg_fare': f"{avg_fare:.0f} KES",
        'deliveries_by_store': list(deliveries_by_store),
        'deliveries_by_hour': deliveries_by_hour,
        'deliveries_by_status': list(deliveries_by_status),
        'heatmap_data': json.dumps(heatmap_data),
        'days': days,
    }
    
    return render(request, 'deliveries/dashboard.html', context)
