from django.conf import settings
from core.models import Notification


def unread_notifications(request):
    """Inject unread notification count into every template."""
    if request.user.is_authenticated:
        count = Notification.objects.filter(user=request.user, is_read=False).count()
        return {'unread_notif_count': count}
    return {'unread_notif_count': 0}


def google_maps(request):
    """Inject Google Maps API key into all templates."""
    return {
        'GOOGLE_MAPS_API_KEY': getattr(settings, 'GOOGLE_MAPS_API_KEY', '')
    }


def admin_stats(request):
    """Inject high-level platform KPI stats when viewing admin pages."""
    if request.path.startswith('/admin/') and getattr(request, 'user', None) and request.user.is_authenticated and (request.user.is_staff or request.user.is_superuser):
        try:
            from core.models import User, Listing, Booking, Payment
            from django.db.models import Sum
            return {
                'admin_kpi': {
                    'total_users': User.objects.count(),
                    'total_listings': Listing.objects.count(),
                    'active_listings': Listing.objects.filter(is_available=True).count(),
                    'pending_verifications': User.objects.filter(verification_status='pending').count(),
                    'total_bookings': Booking.objects.count(),
                    'confirmed_bookings': Booking.objects.filter(status='confirmed').count(),
                    'total_revenue': Payment.objects.filter(status='completed').aggregate(total=Sum('amount'))['total'] or 0,
                }
            }
        except Exception:
            return {}
    return {}


