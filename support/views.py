from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Count, Q
from django.utils import timezone
from .models import SupportTicket, TicketReply

# ── helpers ──────────────────────────────────────────────────────────────────
def is_staff(user):
    return user.is_authenticated and (user.is_staff or user.is_superuser)

staff_required = user_passes_test(is_staff, login_url='/support/login/')


# ═══════════════════════════════════════════════════════════════════════════
# PORTAL AUTH
# ═══════════════════════════════════════════════════════════════════════════

def portal_login(request):
    if request.user.is_authenticated and is_staff(request.user):
        return redirect('portal_dashboard')
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        user = authenticate(request, username=username, password=password)
        if user and is_staff(user):
            login(request, user)
            return redirect('portal_dashboard')
        elif user:
            messages.error(request, 'Access denied — staff accounts only.')
        else:
            messages.error(request, 'Invalid username or password.')
    return render(request, 'support/portal_login.html')


def portal_logout(request):
    logout(request)
    return redirect('portal_login')


# ═══════════════════════════════════════════════════════════════════════════
# USER-FACING VIEWS  (main site)
# ═══════════════════════════════════════════════════════════════════════════

@login_required
def submit_ticket(request):
    if request.method == 'POST':
        subject  = request.POST.get('subject', '').strip()
        message  = request.POST.get('message', '').strip()
        category = request.POST.get('category', 'other')
        if not subject or not message:
            messages.error(request, 'Please fill in all fields.')
        else:
            ticket = SupportTicket.objects.create(
                user=request.user, subject=subject, message=message, category=category,
            )
            messages.success(request, f'Ticket #{ticket.pk} submitted! We\'ll reply soon.')
            return redirect('my_tickets')
    return render(request, 'support/submit_ticket.html', {'categories': SupportTicket.CATEGORY_CHOICES})


@login_required
def my_tickets(request):
    tickets = SupportTicket.objects.filter(user=request.user)
    return render(request, 'support/my_tickets.html', {'tickets': tickets})


@login_required
def ticket_detail_user(request, pk):
    from django.shortcuts import get_object_or_404
    ticket = get_object_or_404(SupportTicket, pk=pk, user=request.user)
    if request.method == 'POST':
        msg = request.POST.get('message', '').strip()
        if msg:
            TicketReply.objects.create(ticket=ticket, author=request.user, message=msg, is_staff=False)
            ticket.status = 'in_progress'
            ticket.save()
            messages.success(request, 'Reply sent.')
        return redirect('ticket_detail_user', pk=pk)
    return render(request, 'support/ticket_detail_user.html', {'ticket': ticket})


# ═══════════════════════════════════════════════════════════════════════════
# STAFF / DEVELOPER PORTAL VIEWS
# ═══════════════════════════════════════════════════════════════════════════

@staff_required
def portal_dashboard(request):
    from core.models import User as CoreUser, Listing, Booking
    total      = SupportTicket.objects.count()
    open_count = SupportTicket.objects.filter(status='open').count()
    urgent     = SupportTicket.objects.filter(priority='urgent', status__in=['open','in_progress']).count()
    resolved   = SupportTicket.objects.filter(status='resolved').count()
    users_total    = CoreUser.objects.count()
    users_today    = CoreUser.objects.filter(date_joined__date=timezone.now().date()).count()
    listings_total = Listing.objects.count()
    bookings_total = Booking.objects.count()
    bookings_today = Booking.objects.filter(created_at__date=timezone.now().date()).count()
    recent_tickets = SupportTicket.objects.select_related('user').order_by('-created_at')[:10]
    return render(request, 'support/portal_dashboard.html', {
        'total': total, 'open_count': open_count, 'urgent': urgent, 'resolved': resolved,
        'users_total': users_total, 'users_today': users_today,
        'listings_total': listings_total,
        'bookings_total': bookings_total, 'bookings_today': bookings_today,
        'recent_tickets': recent_tickets,
    })


@staff_required
def portal_tickets(request):
    status   = request.GET.get('status', '')
    priority = request.GET.get('priority', '')
    category = request.GET.get('category', '')
    q        = request.GET.get('q', '')
    tickets = SupportTicket.objects.select_related('user', 'assigned_to')
    if status:   tickets = tickets.filter(status=status)
    if priority: tickets = tickets.filter(priority=priority)
    if category: tickets = tickets.filter(category=category)
    if q:        tickets = tickets.filter(Q(subject__icontains=q) | Q(user__username__icontains=q))
    return render(request, 'support/portal_tickets.html', {
        'tickets': tickets,
        'status_choices': SupportTicket.STATUS_CHOICES,
        'priority_choices': SupportTicket.PRIORITY_CHOICES,
        'category_choices': SupportTicket.CATEGORY_CHOICES,
        'filters': {'status': status, 'priority': priority, 'category': category, 'q': q},
    })


@staff_required
def portal_ticket_detail(request, pk):
    from django.shortcuts import get_object_or_404
    ticket = get_object_or_404(SupportTicket, pk=pk)
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'reply':
            msg = request.POST.get('message', '').strip()
            if msg:
                TicketReply.objects.create(ticket=ticket, author=request.user, message=msg, is_staff=True)
                ticket.status = 'in_progress'
                ticket.save()
                messages.success(request, 'Reply sent.')
        elif action == 'status':
            new_status = request.POST.get('status')
            if new_status in dict(SupportTicket.STATUS_CHOICES):
                ticket.status = new_status
                ticket.save()
                messages.success(request, f'Status → {ticket.get_status_display()}')
        elif action == 'priority':
            new_priority = request.POST.get('priority')
            if new_priority in dict(SupportTicket.PRIORITY_CHOICES):
                ticket.priority = new_priority
                ticket.save()
                messages.success(request, f'Priority → {ticket.get_priority_display()}')
        return redirect('portal_ticket_detail', pk=pk)
    return render(request, 'support/portal_ticket_detail.html', {
        'ticket': ticket,
        'status_choices': SupportTicket.STATUS_CHOICES,
        'priority_choices': SupportTicket.PRIORITY_CHOICES,
    })


@staff_required
def portal_users(request):
    from core.models import User as CoreUser
    from django.shortcuts import get_object_or_404
    q = request.GET.get('q', '')
    role_filter = request.GET.get('role', '')
    users = CoreUser.objects.order_by('-date_joined')
    if q:
        users = users.filter(Q(username__icontains=q) | Q(email__icontains=q) | Q(phone__icontains=q))
    if role_filter:
        users = users.filter(role=role_filter)
    if request.method == 'POST':
        uid    = request.POST.get('user_id')
        action = request.POST.get('action')
        user   = get_object_or_404(CoreUser, pk=uid)
        if action == 'ban':
            user.is_active = False; user.save()
            messages.success(request, f'{user.username} has been banned.')
        elif action == 'unban':
            user.is_active = True; user.save()
            messages.success(request, f'{user.username} has been unbanned.')
        elif action == 'make_staff':
            user.is_staff = True; user.save()
            messages.success(request, f'{user.username} is now a staff member.')
        elif action == 'verify_phone':
            user.phone_verified = True; user.save()
            messages.success(request, f'{user.username} phone manually verified.')
        return redirect('portal_users')
    return render(request, 'support/portal_users.html', {'users': users, 'q': q, 'role_filter': role_filter})


@staff_required
def portal_user_detail(request, pk):
    """Staff views full user profile with verification controls."""
    from core.models import User as CoreUser
    from django.shortcuts import get_object_or_404
    user = get_object_or_404(CoreUser, pk=pk)

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'verify_phone':
            user.phone_verified = True
            user.save()
            messages.success(request, f'✅ Phone verified for {user.username}.')

        elif action == 'unverify_phone':
            user.phone_verified = False
            user.save()
            messages.success(request, f'Phone verification removed for {user.username}.')

        elif action == 'approve_id':
            user.verification_status = 'approved'
            user.is_verified = True
            user.save()
            messages.success(request, f'✅ ID document approved for {user.username}.')

        elif action == 'reject_id':
            user.verification_status = 'rejected'
            user.is_verified = False
            user.save()
            messages.success(request, f'❌ ID document rejected for {user.username}.')

        elif action == 'reset_id':
            user.verification_status = 'not_submitted'
            user.is_verified = False
            user.save()
            messages.success(request, f'ID verification reset for {user.username}.')

        elif action == 'verify_guest':
            user.is_verified = True
            user.save()
            messages.success(request, f'✅ Guest {user.username} manually verified.')

        elif action == 'unverify_guest':
            user.is_verified = False
            user.save()
            messages.success(request, f'Guest verification removed for {user.username}.')

        elif action == 'ban':
            user.is_active = False
            user.save()
            messages.success(request, f'{user.username} has been banned.')

        elif action == 'unban':
            user.is_active = True
            user.save()
            messages.success(request, f'{user.username} has been unbanned.')

        elif action == 'change_role':
            new_role = request.POST.get('role')
            if new_role in ['guest', 'owner']:
                user.role = new_role
                user.save()
                messages.success(request, f'{user.username} role changed to {new_role}.')

        return redirect('portal_user_detail', pk=pk)

    tickets = user.tickets.order_by('-created_at')[:5]
    return render(request, 'support/portal_user_detail.html', {
        'u': user,
        'tickets': tickets,
    })


@staff_required
def portal_reports(request):
    """Staff views all listing reports (fake, scam, etc)."""
    from core.models import Report
    status_filter = request.GET.get('status', '')
    reports = Report.objects.select_related('listing', 'reporter').order_by('-created_at')
    if status_filter:
        reports = reports.filter(status=status_filter)

    if request.method == 'POST':
        rid    = request.POST.get('report_id')
        action = request.POST.get('action')
        report = get_object_or_404(Report, pk=rid)

        if action == 'mark_reviewed':
            report.status = 'reviewed'
            report.save()
            messages.success(request, f'Report #{rid} marked as reviewed.')
        elif action == 'dismiss':
            report.status = 'dismissed'
            report.save()
            messages.success(request, f'Report #{rid} dismissed.')
        elif action == 'deactivate_listing':
            report.listing.is_available = False
            report.listing.save()
            report.status = 'reviewed'
            report.save()
            messages.success(request, f'Listing "{report.listing.title}" deactivated.')
        elif action == 'reopen':
            report.status = 'open'
            report.save()
            messages.success(request, f'Report #{rid} reopened.')
        return redirect('portal_reports')

    open_count     = Report.objects.filter(status='open').count()
    reviewed_count = Report.objects.filter(status='reviewed').count()
    dismissed_count= Report.objects.filter(status='dismissed').count()
    return render(request, 'support/portal_reports.html', {
        'reports': reports,
        'open_count': open_count,
        'reviewed_count': reviewed_count,
        'dismissed_count': dismissed_count,
        'status_filter': status_filter,
    })


@staff_required
def portal_verifications(request):
    """Staff Portal view specifically for reviewing uploaded Owner ID documents with image previews."""
    from core.models import User as CoreUser, Notification
    from django.shortcuts import get_object_or_404

    status_filter = request.GET.get('status', 'pending')
    users_with_id = CoreUser.objects.exclude(id_proof='').order_by('-date_joined')

    if status_filter in ('pending', 'approved', 'rejected'):
        users_with_id = users_with_id.filter(verification_status=status_filter)

    if request.method == 'POST':
        uid = request.POST.get('user_id')
        action = request.POST.get('action')
        u = get_object_or_404(CoreUser, pk=uid)

        if action == 'approve':
            u.verification_status = 'approved'
            u.is_verified = True
            u.save()
            Notification.objects.create(
                user=u,
                title='ID Verification Approved ✅',
                message='Your ID proof document has been verified and approved by Support Staff. You can now post room listings!'
            )
            messages.success(request, f'✅ ID Proof approved for {u.username}.')
        elif action == 'reject':
            u.verification_status = 'rejected'
            u.is_verified = False
            u.save()
            Notification.objects.create(
                user=u,
                title='ID Verification Update ❌',
                message='Your ID proof document could not be verified. Please re-upload a clear ID document.'
            )
            messages.success(request, f'❌ ID Proof rejected for {u.username}.')
        elif action == 'reset':
            u.verification_status = 'pending'
            u.save()
            messages.success(request, f'Reset verification status for {u.username}.')

        return redirect(f"/support/portal/verifications/?status={status_filter}")

    pending_count  = CoreUser.objects.exclude(id_proof='').filter(verification_status='pending').count()
    approved_count = CoreUser.objects.exclude(id_proof='').filter(verification_status='approved').count()
    rejected_count = CoreUser.objects.exclude(id_proof='').filter(verification_status='rejected').count()

    return render(request, 'support/portal_verifications.html', {
        'users': users_with_id,
        'status_filter': status_filter,
        'pending_count': pending_count,
        'approved_count': approved_count,
        'rejected_count': rejected_count,
    })

