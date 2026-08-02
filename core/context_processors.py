from core.models import Notification


def unread_notifications(request):
    """Inject unread notification count into every template."""
    if request.user.is_authenticated:
        count = Notification.objects.filter(user=request.user, is_read=False).count()
        return {'unread_notif_count': count}
    return {'unread_notif_count': 0}
