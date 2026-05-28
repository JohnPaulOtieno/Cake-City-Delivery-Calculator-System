from django.conf import settings


def google_maps_key(request):
    """Inject GOOGLE_MAPS_API_KEY into every template context."""
    return {
        'GOOGLE_MAPS_API_KEY': settings.GOOGLE_MAPS_API_KEY,
    }
