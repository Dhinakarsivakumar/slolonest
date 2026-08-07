from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Q, F
from django.utils import timezone
from datetime import date
import json
import random

from .models import User, Listing, ListingImage, Booking, Message, Review, OTPCode, Payment, Notification, Favorite, Report
from .forms import SignUpForm, ListingForm, BookingForm, MessageForm, ReviewForm, ReportForm


# Diagnostic endpoint for OAuth configuration
from django.http import JsonResponse
def test_oauth(request):
    from django.contrib.sites.models import Site
    from allauth.socialaccount.models import SocialApp
    
    sites_info = []
    for site in Site.objects.all():
        sites_info.append({'id': site.id, 'domain': site.domain, 'name': site.name})
        
    apps_info = []
    for app in SocialApp.objects.all():
        apps_info.append({
            'provider': app.provider,
            'name': app.name,
            'client_id_starts_with': app.client_id[:15] if app.client_id else None,
            'secret_starts_with': app.secret[:5] if app.secret else None,
            'linked_sites': [s.domain for s in app.sites.all()]
        })
        
    return JsonResponse({
        'current_site_id_setting': getattr(request, 'site', None).id if hasattr(request, 'site') else 'No request.site attribute',
        'sites_in_database': sites_info,
        'social_apps_configured': apps_info,
        'google_client_id_env_present': bool(os.environ.get('GOOGLE_CLIENT_ID')),
        'google_client_secret_env_present': bool(os.environ.get('GOOGLE_CLIENT_SECRET')),
    })


# ─────────────────────────────────────────────────────────────
# HOME / SEARCH
# ─────────────────────────────────────────────────────────────


def home(request):
    # Prefetch images to avoid N+1 queries on card grid
    listings = Listing.objects.filter(is_available=True).prefetch_related('images')

    city      = request.GET.get('city',      '').strip()
    room_type = request.GET.get('room_type', '')
    gender    = request.GET.get('gender',    '')
    stay_type = request.GET.get('stay_type', '')
    min_price = request.GET.get('min_price', '')
    max_price = request.GET.get('max_price', '')
    check_in  = request.GET.get('check_in',  '')
    check_out = request.GET.get('check_out', '')
    wifi      = request.GET.get('wifi',      '')
    ac        = request.GET.get('ac',        '')
    food      = request.GET.get('food',      '')
    parking   = request.GET.get('parking',   '')

    if city:
        listings = listings.filter(Q(city__icontains=city) | Q(area__icontains=city))
    if room_type:
        listings = listings.filter(room_type=room_type)
    if gender:
        listings = listings.filter(Q(gender_preference=gender) | Q(gender_preference='any'))
    if stay_type:
        listings = listings.filter(Q(stay_type=stay_type) | Q(stay_type='both'))
    if wifi:
        listings = listings.filter(wifi=True)
    if ac:
        listings = listings.filter(ac=True)
    if food:
        listings = listings.filter(food_included=True)
    if parking:
        listings = listings.filter(parking=True)
    if min_price:
        try:
            listings = listings.filter(
                Q(price_per_day__gte=float(min_price)) | Q(price_per_day__isnull=True)
            )
        except ValueError:
            pass
    if max_price:
        try:
            listings = listings.filter(
                Q(price_per_day__lte=float(max_price)) | Q(price_per_day__isnull=True)
            )
        except ValueError:
            pass

    # BUG FIX #1: Actually filter by dates (was accepted but ignored before)
    if check_in and check_out:
        try:
            from datetime import datetime
            ci = datetime.strptime(check_in,  '%Y-%m-%d').date()
            co = datetime.strptime(check_out, '%Y-%m-%d').date()
            if ci >= co:
                messages.error(request, 'Check-out must be after check-in.')
            else:
                booked_ids = Booking.objects.filter(
                    status__in=['requested', 'approved'],
                    check_in__lt=co,
                    check_out__gt=ci,
                ).values_list('listing_id', flat=True)
                listings = listings.exclude(pk__in=booked_ids)
        except ValueError:
            pass

    listings = listings.order_by('-is_verified', '-created_at')

    popular_cities = (
        Listing.objects.filter(is_available=True)
        .exclude(city='')
        .values_list('city', flat=True)
        .distinct()
        .order_by('city')[:8]
    )

    map_points = [
        {
            'id': l.pk, 'title': l.title,
            'lat': l.latitude, 'lng': l.longitude,
            'price': float(l.price_per_day) if l.price_per_day else (
                     float(l.price_per_month) if l.price_per_month else None),
            'url': l.get_absolute_url(),
        }
        for l in listings if l.latitude is not None and l.longitude is not None
    ]

    favorited_ids = set()
    if request.user.is_authenticated:
        favorited_ids = set(
            Favorite.objects.filter(user=request.user).values_list('listing_id', flat=True)
        )

    context = {
        'listings': listings,
        'filters': request.GET,
        'popular_cities': popular_cities,
        'map_points_json': json.dumps(map_points),
        'favorited_ids': favorited_ids,
    }
    return render(request, 'core/home.html', context)


# ─────────────────────────────────────────────────────────────
# LISTING DETAIL
# ─────────────────────────────────────────────────────────────

def listing_detail(request, pk):
    listing = get_object_or_404(Listing.objects.prefetch_related('images'), pk=pk)

    # BUG FIX #2: Don't count owner's own views; use session dedup
    session_key = f'viewed_listing_{pk}'
    if not request.session.get(session_key) and (
        not request.user.is_authenticated or request.user != listing.owner
    ):
        Listing.objects.filter(pk=pk).update(views_count=F('views_count') + 1)
        request.session[session_key] = True

    booking_form = BookingForm()
    is_favorited = (
        request.user.is_authenticated
        and Favorite.objects.filter(user=request.user, listing=listing).exists()
    )
    reviews = Review.objects.filter(
        booking__listing=listing, review_type='guest_to_owner'
    ).select_related('reviewer').order_by('-created_at')[:5]
    avg_rating = listing.average_rating()

    return render(request, 'core/listing_detail.html', {
        'listing': listing,
        'booking_form': booking_form,
        'is_favorited': is_favorited,
        'reviews': reviews,
        'avg_rating': avg_rating,
    })


# ─────────────────────────────────────────────────────────────
# AUTH
# ─────────────────────────────────────────────────────────────

def signup(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            messages.success(request, 'Welcome to SoloNest! Your account is ready.')
            return redirect('dashboard')
    else:
        form = SignUpForm()
    return render(request, 'core/signup.html', {'form': form})


@login_required
def post_login_redirect(request):
    """After any login (password or Google), send new/incomplete profiles
    to fill in role + phone before landing on dashboard."""
    if not request.user.phone:
        return redirect('profile_settings')
    return redirect('dashboard')


# ─────────────────────────────────────────────────────────────
# PROFILE / SETTINGS
# ─────────────────────────────────────────────────────────────

@login_required
def profile_settings(request):
    if request.method == 'POST':
        role  = request.POST.get('role')
        phone = request.POST.get('phone', '').strip()
        if role in ('guest', 'owner'):
            request.user.role = role
        request.user.phone = phone
        request.user.save()
        messages.success(request, 'Profile updated successfully.')
        return redirect('dashboard')
    return render(request, 'core/profile_settings.html')


# ─────────────────────────────────────────────────────────────
# HELP PAGE
# ─────────────────────────────────────────────────────────────

def help_page(request):
    return render(request, 'core/help.html')


# ─────────────────────────────────────────────────────────────
# DASHBOARD
# ─────────────────────────────────────────────────────────────

@login_required
def dashboard(request):
    if request.user.role == 'owner':
        listings = Listing.objects.filter(owner=request.user).prefetch_related('images')
        bookings = Booking.objects.filter(
            listing__owner=request.user
        ).select_related('listing', 'guest').order_by('-created_at')
        return render(request, 'core/dashboard_owner.html', {
            'listings': listings, 'bookings': bookings
        })
    else:
        bookings = Booking.objects.filter(
            guest=request.user
        ).select_related('listing').order_by('-created_at')
        return render(request, 'core/dashboard_guest.html', {'bookings': bookings})


# ─────────────────────────────────────────────────────────────
# LISTING MANAGEMENT  (BUG FIXES: validation, guards)
# ─────────────────────────────────────────────────────────────

@login_required
def add_listing(request):
    if request.user.role != 'owner':
        messages.error(request, 'Only owners can add listings. Update your role in profile settings.')
        return redirect('profile_settings')

    if request.method == 'POST':
        form = ListingForm(request.POST)
        if form.is_valid():
            # BUG FIX #3: At least one price must be provided
            price_day   = form.cleaned_data.get('price_per_day')
            price_month = form.cleaned_data.get('price_per_month')
            if not price_day and not price_month:
                messages.error(request, 'Please set at least one price (per day or per month).')
                return render(request, 'core/listing_form.html', {'form': form})

            listing = form.save(commit=False)
            listing.owner = request.user
            listing.save()
            photos = request.FILES.getlist('photos')
            for f in photos:
                # BUG FIX #4: Server-side image type validation
                if not f.content_type.startswith('image/'):
                    messages.warning(request, f'"{f.name}" is not a valid image and was skipped.')
                    continue
                ListingImage.objects.create(listing=listing, image=f)
            messages.success(request, '🎉 Your room has been listed! It will be verified by our team shortly.')
            return redirect('listing_detail', pk=listing.pk)
    else:
        form = ListingForm()
    return render(request, 'core/listing_form.html', {'form': form})


@login_required
def edit_listing(request, pk):
    listing = get_object_or_404(Listing, pk=pk)
    if listing.owner != request.user:
        messages.error(request, 'You can only edit your own listings.')
        return redirect('dashboard')

    if request.method == 'POST':
        form = ListingForm(request.POST, instance=listing)
        if form.is_valid():
            price_day   = form.cleaned_data.get('price_per_day')
            price_month = form.cleaned_data.get('price_per_month')
            if not price_day and not price_month:
                messages.error(request, 'Please set at least one price (per day or per month).')
                return render(request, 'core/listing_form.html', {'form': form, 'listing': listing, 'editing': True})
            form.save()
            for f in request.FILES.getlist('photos'):
                if not f.content_type.startswith('image/'):
                    messages.warning(request, f'"{f.name}" is not a valid image and was skipped.')
                    continue
                ListingImage.objects.create(listing=listing, image=f)
            messages.success(request, 'Listing updated.')
            return redirect('listing_detail', pk=listing.pk)
    else:
        form = ListingForm(instance=listing)
    return render(request, 'core/listing_form.html', {'form': form, 'listing': listing, 'editing': True})


@login_required
def delete_listing(request, pk):
    listing = get_object_or_404(Listing, pk=pk)
    if listing.owner != request.user:
        messages.error(request, 'You can only delete your own listings.')
        return redirect('dashboard')
    if request.method == 'POST':
        listing.delete()
        messages.success(request, 'Listing deleted successfully.')
        return redirect('dashboard')
    return render(request, 'core/listing_confirm_delete.html', {'listing': listing})


# ─────────────────────────────────────────────────────────────
# BOOKING  (BUG FIXES: availability, past dates, self-booking)
# ─────────────────────────────────────────────────────────────

@login_required
def request_booking(request, pk):
    listing = get_object_or_404(Listing, pk=pk)

    # BUG FIX #5: Room must be available
    if not listing.is_available:
        messages.error(request, 'Sorry, this room is currently not available for booking.')
        return redirect('listing_detail', pk=pk)

    # BUG FIX #6: Owner cannot book their own room
    if request.user == listing.owner:
        messages.error(request, 'You cannot book your own room.')
        return redirect('listing_detail', pk=pk)

    if request.method == 'POST':
        form = BookingForm(request.POST)
        if form.is_valid():
            check_in  = form.cleaned_data['check_in']
            check_out = form.cleaned_data['check_out']
            today     = date.today()

            # BUG FIX #7: No past-date bookings
            if check_in < today:
                messages.error(request, 'Check-in date cannot be in the past.')
                return redirect('listing_detail', pk=pk)

            # BUG FIX #8: check-out must be after check-in
            if check_out <= check_in:
                messages.error(request, 'Check-out must be after check-in.')
                return redirect('listing_detail', pk=pk)

            # BUG FIX #9: Overlap detection (double-booking prevention)
            overlap = Booking.objects.filter(
                listing=listing,
                status__in=['requested', 'approved'],
                check_in__lt=check_out,
                check_out__gt=check_in,
            ).exists()
            if overlap:
                messages.error(
                    request,
                    'Those dates overlap with an existing booking for this room. Please choose different dates.'
                )
                return redirect('listing_detail', pk=pk)

            booking = form.save(commit=False)
            booking.listing = listing
            booking.guest   = request.user
            booking.save()
            notify(
                listing.owner,
                f'New booking request for "{listing.title}" from {request.user.username}.',
                f'/booking/{booking.pk}/'
            )
            messages.success(request, 'Booking request sent! The owner will review it shortly.')
            return redirect('booking_detail', pk=booking.pk)
    return redirect('listing_detail', pk=pk)


@login_required
def cancel_booking(request, pk):
    """BUG FIX #10: Allow guest to cancel a pending booking."""
    booking = get_object_or_404(Booking, pk=pk, guest=request.user)
    if booking.status not in ('requested', 'approved'):
        messages.error(request, 'This booking cannot be cancelled anymore.')
        return redirect('booking_detail', pk=pk)
    if request.method == 'POST':
        booking.status = 'cancelled'
        booking.save()
        notify(
            booking.listing.owner,
            f'{request.user.username} cancelled their booking for "{booking.listing.title}".',
            f'/booking/{booking.pk}/'
        )
        messages.success(request, 'Booking cancelled.')
        return redirect('dashboard')
    return render(request, 'core/booking_cancel_confirm.html', {'booking': booking})


@login_required
def booking_detail(request, pk):
    booking = get_object_or_404(Booking, pk=pk)
    if request.user not in (booking.guest, booking.listing.owner):
        messages.error(request, "You don't have access to this booking.")
        return redirect('dashboard')

    if request.method == 'POST':
        if 'send_message' in request.POST:
            msg_form = MessageForm(request.POST)
            if msg_form.is_valid():
                m = msg_form.save(commit=False)
                m.booking = booking
                m.sender  = request.user
                m.save()
                return redirect('booking_detail', pk=booking.pk)

        elif 'approve' in request.POST and request.user == booking.listing.owner:
            # BUG FIX #11: Don't approve past-date bookings
            if booking.check_out < date.today():
                messages.error(request, 'Cannot approve a booking with past dates.')
            else:
                booking.status = 'approved'
                booking.save()
                notify(booking.guest, f'Your booking for "{booking.listing.title}" was approved!', f'/booking/{booking.pk}/')
                messages.success(request, 'Booking approved.')

        elif 'reject' in request.POST and request.user == booking.listing.owner:
            booking.status = 'rejected'
            booking.save()
            notify(booking.guest, f'Your booking for "{booking.listing.title}" was declined.', f'/booking/{booking.pk}/')
            messages.success(request, 'Booking rejected.')

        elif 'complete' in request.POST and request.user == booking.listing.owner:
            booking.status = 'completed'
            booking.save()
            notify(booking.guest, f'Your stay at "{booking.listing.title}" is marked complete — please leave a review!', f'/booking/{booking.pk}/')
            messages.success(request, 'Stay marked as completed.')

        return redirect('booking_detail', pk=booking.pk)

    msg_form     = MessageForm()
    review_form  = ReviewForm()
    chat_messages = booking.messages.all().select_related('sender')
    already_reviewed = Review.objects.filter(
        booking=booking,
        review_type='guest_to_owner' if request.user == booking.guest else 'owner_to_guest'
    ).exists()

    return render(request, 'core/booking_detail.html', {
        'booking': booking,
        'msg_form': msg_form,
        'review_form': review_form,
        'chat_messages': chat_messages,
        'already_reviewed': already_reviewed,
    })


@login_required
def add_review(request, pk):
    booking = get_object_or_404(Booking, pk=pk)
    if booking.status != 'completed':
        messages.error(request, 'You can only review completed stays.')
        return redirect('booking_detail', pk=pk)

    review_type = 'guest_to_owner' if request.user == booking.guest else 'owner_to_guest'

    # BUG FIX #12: Prevent duplicate review crash (was IntegrityError → 500)
    if Review.objects.filter(booking=booking, review_type=review_type).exists():
        messages.warning(request, 'You have already submitted a review for this booking.')
        return redirect('booking_detail', pk=pk)

    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.booking     = booking
            review.reviewer    = request.user
            review.review_type = review_type
            review.save()
            messages.success(request, 'Thank you for your review!')
    return redirect('booking_detail', pk=pk)


# ─────────────────────────────────────────────────────────────
# NOTIFICATIONS HELPER
# ─────────────────────────────────────────────────────────────

def notify(user, message, link=''):
    """Create an in-app notification and fire an email (console backend in dev)."""
    Notification.objects.create(user=user, message=message, link=link)
    try:
        from django.core.mail import send_mail
        from django.conf import settings as dj_settings
        if user.email:
            send_mail(
                subject='SoloNest update',
                message=message + (f'\n\nView: http://127.0.0.1:8000{link}' if link else ''),
                from_email=dj_settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=True,
            )
    except Exception:
        pass


@login_required
def notifications_list(request):
    notifs = Notification.objects.filter(user=request.user).order_by('-created_at')
    # BUG FIX #13: Mark all as read when page is viewed
    notifs.filter(is_read=False).update(is_read=True)
    return render(request, 'core/notifications.html', {'notifications': notifs})


# ─────────────────────────────────────────────────────────────
# OTP / PHONE VERIFICATION
# ─────────────────────────────────────────────────────────────

def _send_sms_otp(phone, code):
    """
    Send OTP via Fast2SMS — authorization sent as HTTP header.
    Returns (success: bool, error_msg: str|None)
    """
    import re, urllib.request, urllib.parse, json
    from django.conf import settings as dj_settings

    api_key = getattr(dj_settings, 'FAST2SMS_API_KEY', '') or ''

    digits = re.sub(r'\D', '', phone)
    if digits.startswith('91') and len(digits) == 12:
        digits = digits[2:]
    if len(digits) != 10:
        return False, 'Invalid phone number — must be 10 digits.'

    if not api_key or getattr(dj_settings, 'OTP_DEV_MODE', True):
        print(f'[DEV OTP] Phone: {phone}  Code: {code}')
        return True, None

    try:
        payload = urllib.parse.urlencode({
            'route':            'otp',
            'variables_values': code,
            'flash':            0,
            'numbers':          digits,
        }).encode()
        req = urllib.request.Request(
            'https://www.fast2sms.com/dev/bulkV2',
            data=payload,
            # authorization goes in HEADER not body
            headers={'authorization': api_key, 'Cache-Control': 'no-cache'},
            method='POST',
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
            if data.get('return'):
                return True, None
            return False, data.get('message', 'SMS failed.')
    except Exception as exc:
        return False, str(exc)


def _send_email_otp(user, code):
    """Free email OTP fallback — works immediately with no payment."""
    from django.core.mail import send_mail
    from django.conf import settings as dj_settings
    try:
        send_mail(
            subject='Your SoloNest OTP Code',
            message=(
                f'Hi {user.username},\n\n'
                f'Your SoloNest verification code is:\n\n'
                f'  {code}\n\n'
                f'This code expires in 10 minutes. Do not share it with anyone.\n\n'
                f'\u2014 SoloNest Team'
            ),
            from_email=dj_settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )
        return True, None
    except Exception as exc:
        return False, str(exc)


@login_required
def send_otp(request):
    if not request.user.phone:
        messages.error(request, 'Add a phone number in your profile first.')
        return redirect('profile_settings')

    from django.core.cache import cache
    rate_key = f'otp_rate_{request.user.pk}'
    if cache.get(rate_key):
        messages.error(request, 'Please wait 60 seconds before requesting another OTP.')
        return render(request, 'core/verify_otp.html', {'dev_code': None})

    OTPCode.objects.filter(user=request.user, is_used=False).update(is_used=True)
    code = f'{random.randint(0, 999999):06d}'
    OTPCode.objects.create(user=request.user, code=code)
    cache.set(rate_key, 1, timeout=60)

    from django.conf import settings as dj_settings
    dev_mode = getattr(dj_settings, 'OTP_DEV_MODE', True)
    dev_code = code if dev_mode else None
    channel = None

    # Try SMS first, fall back to email automatically
    sms_ok, sms_err = _send_sms_otp(request.user.phone, code)
    if sms_ok and not dev_mode:
        messages.success(request, f'OTP sent to {request.user.phone} via SMS ✓')
        channel = 'sms'
    else:
        # SMS failed — try email fallback
        email_ok, email_err = _send_email_otp(request.user, code)
        if email_ok and not dev_mode:
            messages.success(request, f'OTP sent to {request.user.email} via Email ✓')
            channel = 'email'
        elif not dev_mode:
            # Both failed — show code on screen as last resort
            messages.warning(request, 'Could not send OTP — here is your code directly.')
            dev_code = code

    return render(request, 'core/verify_otp.html', {'dev_code': dev_code, 'channel': channel})


@login_required
def verify_otp(request):
    if request.method == 'POST':
        entered = request.POST.get('code', '').strip()
        otp = OTPCode.objects.filter(user=request.user, is_used=False).order_by('-created_at').first()
        if not otp:
            messages.error(request, 'No OTP found — request a new one.')
        elif otp.is_expired():
            messages.error(request, 'That code expired — request a new one.')
        elif otp.code != entered:
            # BUG FIX #14: Track failed attempts to prevent brute-force
            if not hasattr(otp, '_attempts'):
                from django.core.cache import cache
                key = f'otp_attempts_{request.user.pk}'
                attempts = cache.get(key, 0) + 1
                cache.set(key, attempts, timeout=600)
                if attempts >= 5:
                    otp.is_used = True
                    otp.save()
                    cache.delete(key)
                    messages.error(request, 'Too many wrong attempts. Request a new OTP.')
                else:
                    messages.error(request, f'Incorrect code. {5 - attempts} attempt(s) left.')
        else:
            from django.core.cache import cache
            cache.delete(f'otp_attempts_{request.user.pk}')
            otp.is_used = True
            otp.save()
            request.user.phone_verified = True
            request.user.save()
            messages.success(request, 'Phone number verified successfully!')
            return redirect('profile_settings')
    return render(request, 'core/verify_otp.html', {'dev_code': None})


# ─────────────────────────────────────────────────────────────
# IDENTITY VERIFICATION
# ─────────────────────────────────────────────────────────────

@login_required
def submit_verification(request):
    if request.method == 'POST' and request.FILES.get('id_proof'):
        f = request.FILES['id_proof']
        # Basic file-type guard
        allowed = ['image/jpeg', 'image/png', 'image/gif', 'application/pdf']
        if f.content_type not in allowed:
            messages.error(request, 'Only JPG, PNG, or PDF files are accepted for ID proof.')
            return render(request, 'core/submit_verification.html')
        request.user.id_proof = f
        request.user.verification_status = 'pending'
        request.user.save()
        messages.success(request, 'ID submitted — an admin will review it soon.')
        return redirect('profile_settings')
    return render(request, 'core/submit_verification.html')


# ─────────────────────────────────────────────────────────────
# FAVORITES
# ─────────────────────────────────────────────────────────────

@login_required
def toggle_favorite(request, pk):
    listing = get_object_or_404(Listing, pk=pk)
    fav, created = Favorite.objects.get_or_create(user=request.user, listing=listing)
    if not created:
        fav.delete()
    next_url = request.POST.get('next') or request.GET.get('next') or 'home'
    return redirect(next_url)


@login_required
def favorites_list(request):
    favs = Favorite.objects.filter(user=request.user).select_related('listing').prefetch_related('listing__images')
    return render(request, 'core/favorites.html', {'favorites': favs})


# ─────────────────────────────────────────────────────────────
# REPORT LISTING
# ─────────────────────────────────────────────────────────────

@login_required
def report_listing(request, pk):
    listing = get_object_or_404(Listing, pk=pk)
    if request.method == 'POST':
        form = ReportForm(request.POST)
        if form.is_valid():
            report = form.save(commit=False)
            report.listing  = listing
            report.reporter = request.user
            report.save()
            messages.success(request, 'Thank you — our team will review this listing.')
            return redirect('listing_detail', pk=listing.pk)
    else:
        form = ReportForm()
    return render(request, 'core/report_listing.html', {'form': form, 'listing': listing})


# ─────────────────────────────────────────────────────────────
# PAYMENT  (BUG FIX: monthly-only listings = ₹0)
# ─────────────────────────────────────────────────────────────

@login_required
def create_payment(request, pk):
    import razorpay
    from django.conf import settings as dj_settings

    booking = get_object_or_404(Booking, pk=pk)
    if request.user != booking.guest:
        messages.error(request, 'You can only pay for your own booking.')
        return redirect('dashboard')
    if booking.status != 'approved':
        messages.error(request, "This booking isn't approved yet.")
        return redirect('booking_detail', pk=booking.pk)

    nights = (booking.check_out - booking.check_in).days or 1

    # BUG FIX #15: Fall back to monthly price when no daily price set
    if booking.listing.price_per_day:
        amount = float(booking.listing.price_per_day) * nights
    elif booking.listing.price_per_month:
        months = max(nights / 30.0, 1)
        amount = float(booking.listing.price_per_month) * months
    else:
        messages.error(request, 'This listing has no price set. Contact the owner.')
        return redirect('booking_detail', pk=booking.pk)

    amount = round(amount, 2)
    payment, _ = Payment.objects.get_or_create(booking=booking, defaults={'amount': amount})

    razorpay_error = None
    try:
        client = razorpay.Client(auth=(dj_settings.RAZORPAY_KEY_ID, dj_settings.RAZORPAY_KEY_SECRET))
        order = client.order.create({
            'amount': int(amount * 100),
            'currency': 'INR',
            'payment_capture': 1,
        })
        payment.razorpay_order_id = order['id']
        payment.save()
    except Exception as e:
        razorpay_error = str(e)

    return render(request, 'core/payment.html', {
        'booking': booking,
        'payment': payment,
        'razorpay_key': dj_settings.RAZORPAY_KEY_ID,
        'razorpay_error': razorpay_error,
    })


@login_required
def payment_callback(request, pk):
    import razorpay
    from django.conf import settings as dj_settings

    booking = get_object_or_404(Booking, pk=pk)
    payment = booking.payment

    if request.method == 'POST':
        client = razorpay.Client(auth=(dj_settings.RAZORPAY_KEY_ID, dj_settings.RAZORPAY_KEY_SECRET))
        params = {
            'razorpay_order_id':   request.POST.get('razorpay_order_id'),
            'razorpay_payment_id': request.POST.get('razorpay_payment_id'),
            'razorpay_signature':  request.POST.get('razorpay_signature'),
        }
        try:
            client.utility.verify_payment_signature(params)
            payment.razorpay_payment_id = params['razorpay_payment_id']
            payment.razorpay_signature  = params['razorpay_signature']
            payment.status = 'paid'
            payment.save()
            booking.is_paid = True
            booking.save()
            notify(booking.listing.owner, f'Payment received for "{booking.listing.title}".', f'/booking/{booking.pk}/')
            messages.success(request, 'Payment successful! 🎉')
        except Exception:
            payment.status = 'failed'
            payment.save()
            messages.error(request, 'Payment verification failed. Please contact support.')
    return redirect('booking_detail', pk=booking.pk)


# ─────────────────────────────────────────────────────────────
# ANALYTICS
# ─────────────────────────────────────────────────────────────

@login_required
def owner_analytics(request):
    if request.user.role != 'owner':
        messages.error(request, 'Analytics is only for owner accounts.')
        return redirect('dashboard')

    listings = Listing.objects.filter(owner=request.user)
    bookings = Booking.objects.filter(listing__owner=request.user)
    total_views = sum(l.views_count for l in listings)
    completed   = bookings.filter(status='completed')

    # BUG FIX: Use correct price for revenue (same fix as payment)
    revenue = 0
    for b in completed:
        nights = (b.check_out - b.check_in).days or 1
        if b.listing.price_per_day:
            revenue += float(b.listing.price_per_day) * nights
        elif b.listing.price_per_month:
            revenue += float(b.listing.price_per_month) * max(nights / 30.0, 1)

    stats = {
        'total_listings':  listings.count(),
        'total_views':     total_views,
        'total_bookings':  bookings.count(),
        'requested':       bookings.filter(status='requested').count(),
        'approved':        bookings.filter(status='approved').count(),
        'completed':       completed.count(),
        'rejected':        bookings.filter(status='rejected').count(),
        'cancelled':       bookings.filter(status='cancelled').count(),
        'revenue':         round(revenue, 2),
    }
    return render(request, 'core/owner_analytics.html', {'stats': stats, 'listings': listings})


@login_required
def platform_analytics(request):
    if not request.user.is_staff:
        messages.error(request, 'Staff only.')
        return redirect('dashboard')
    stats = {
        'total_users':            User.objects.count(),
        'total_owners':           User.objects.filter(role='owner').count(),
        'total_guests':           User.objects.filter(role='guest').count(),
        'total_listings':         Listing.objects.count(),
        'verified_listings':      Listing.objects.filter(is_verified=True).count(),
        'total_bookings':         Booking.objects.count(),
        'completed_bookings':     Booking.objects.filter(status='completed').count(),
        'open_reports':           Report.objects.filter(status='open').count(),
        'pending_verifications':  User.objects.filter(verification_status='pending').count(),
    }
    return render(request, 'core/platform_analytics.html', {'stats': stats})
