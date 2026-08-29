from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
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
import os
import traceback

def test_oauth(request):
    try:
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
            'status': 'success',
            'current_site_id_setting': getattr(request, 'site', None).id if hasattr(request, 'site') else 'No request.site attribute',
            'sites_in_database': sites_info,
            'social_apps_configured': apps_info,
            'google_client_id_env_present': bool(os.environ.get('GOOGLE_CLIENT_ID')),
            'google_client_secret_env_present': bool(os.environ.get('GOOGLE_CLIENT_SECRET')),
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'error_message': str(e),
            'traceback': traceback.format_exc()
        })



# ─────────────────────────────────────────────────────────────
# HOME / SEARCH
# ─────────────────────────────────────────────────────────────


def home(request):
    # Prefetch images to avoid N+1 queries on card grid (show all available listings to users)
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
        if room_type == 'hotel':
            listings = listings.filter(Q(room_type='hotel') | Q(room_type='private'))
        elif room_type == 'pg':
            listings = listings.filter(Q(room_type__startswith='pg_') | Q(room_type='pg') | Q(room_type='shared'))
        elif room_type == 'homestay':
            listings = listings.filter(Q(room_type__startswith='homestay_') | Q(room_type='homestay') | Q(room_type='guesthouse'))
        elif room_type == 'rental':
            listings = listings.filter(Q(room_type='rental') | Q(room_type='full_house'))
        else:
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

    raw_cities = (
        Listing.objects.filter(is_available=True)
        .exclude(city='')
        .values_list('city', flat=True)
    )
    popular_cities = []
    seen_cities = set()
    for c in raw_cities:
        norm = c.strip().title()
        if norm.lower() != 'thanjavur' and norm.lower() not in seen_cities:
            seen_cities.add(norm.lower())
            popular_cities.append(norm)
    popular_cities = popular_cities[:8]

    favorited_ids = set()
    if request.user.is_authenticated:
        favorited_ids = set(
            Favorite.objects.filter(user=request.user).values_list('listing_id', flat=True)
        )

    context = {
        'listings': listings,
        'filters': request.GET,
        'popular_cities': popular_cities,
        'favorited_ids': favorited_ids,
    }

    if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.GET.get('ajax') == '1':
        return render(request, 'core/partials/listings_grid.html', context)

    return render(request, 'core/home.html', context)



def city_suggestions(request):
    """API view returning matching city names for auto-complete search."""
    q = request.GET.get('q', '').strip()

    # 1. Fetch cities from database
    db_cities = list(
        Listing.objects.filter(is_available=True)
        .exclude(city='')
        .values_list('city', flat=True)
        .distinct()
    )

    # 2. Known popular cities in South India / Tamil Nadu
    popular = [
        'Chennai', 'Coimbatore', 'Madurai', 'Tiruchirappalli', 
        'Salem', 'Tirunelveli', 'Vellore', 'Erode', 'Kanchipuram', 
        'Thoothukudi', 'Nagercoil', 'Dindigul', 'Bengaluru', 'Hyderabad', 'Kochi'
    ]

    all_cities = list(dict.fromkeys(db_cities + popular))

    if q:
        matched = [c for c in all_cities if q.lower() in c.lower()]
    else:
        matched = all_cities[:8]

    return JsonResponse({'cities': matched[:8]})


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


@login_required
def switch_mode(request):
    """Allow owners to quickly toggle between owner and guest modes."""
    if request.user.role == 'owner':
        request.user.role = 'guest'
        request.session['is_original_owner'] = True
        messages.success(request, 'Switched to Guest mode ')
    else:
        if request.session.get('is_original_owner') or request.user.is_verified or request.user.verification_status in ['pending', 'approved']:
            request.user.role = 'owner'
            messages.success(request, 'Switched to Owner mode ')
        else:
            messages.error(request, 'Only verified owners can switch to Owner mode.')
    request.user.save()
    next_url = request.META.get('HTTP_REFERER') or 'dashboard'
    return redirect(next_url)



# ─────────────────────────────────────────────────────────────
# PROFILE / SETTINGS
# ─────────────────────────────────────────────────────────────

@login_required
def profile_settings(request):
    if request.method == 'POST':
        first_name    = request.POST.get('first_name', '').strip()
        last_name     = request.POST.get('last_name', '').strip()
        gender        = request.POST.get('gender', '').strip()
        age_str       = request.POST.get('age', '').strip()
        from_location = request.POST.get('from_location', '').strip()
        bio           = request.POST.get('bio', '').strip()
        role          = request.POST.get('role')
        phone_input   = request.POST.get('phone', '').strip()

        request.user.first_name = first_name
        request.user.last_name = last_name
        request.user.gender = gender
        request.user.from_location = from_location
        request.user.bio = bio

        # Once mobile number is registered, it becomes unchangeable
        if not request.user.phone and phone_input:
            request.user.phone = phone_input

        if age_str.isdigit():
            request.user.age = int(age_str)
        elif not age_str:
            request.user.age = None

        if role in ('guest', 'owner'):
            request.user.role = role

        request.user.save()
        messages.success(request, 'Profile details updated successfully!')
        return redirect('profile_settings')

    return render(request, 'core/profile_settings.html')



# ─────────────────────────────────────────────────────────────
# HELP PAGE
# ─────────────────────────────────────────────────────────────

def help_page(request):
    return render(request, 'core/help.html')


def terms_page(request):
    return render(request, 'core/terms.html')


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
    # Auto-upgrade role to owner if user clicks List Your Room
    if request.user.role != 'owner':
        request.user.role = 'owner'
        request.user.save()
        request.session['is_original_owner'] = True

    # 1. Mandatory Profile Details Check Before Listing
    u = request.user
    if not (u.first_name and u.phone and u.gender and u.age and u.from_location):
        messages.error(
            request,
            'Complete Profile Required: Please fill out all required profile details (First Name, Phone Number, Gender, Age, and Hometown) in Profile Settings before listing a room.'
        )
        return redirect('profile_settings')

    # Owners can enter room details & upload photos FIRST without being blocked!

    if request.method == 'POST':
        form = ListingForm(request.POST)
        if form.is_valid():
            # At least one price must be provided
            price_day   = form.cleaned_data.get('price_per_day')
            price_month = form.cleaned_data.get('price_per_month')
            if not price_day and not price_month:
                messages.error(request, 'Please set at least one price (per day or per month).')
                return render(request, 'core/listing_form.html', {'form': form})

            listing = form.save(commit=False)
            listing.owner = request.user
            
            # If owner is already ID verified, mark listing verified and published
            if request.user.verification_status == 'approved':
                listing.is_verified = True
            else:
                listing.is_verified = False

            listing.save()

            photos = request.FILES.getlist('photos')
            for f in photos:
                if not f.content_type.startswith('image/'):
                    messages.warning(request, f'"{f.name}" is not a valid image and was skipped.')
                    continue
                ListingImage.objects.create(listing=listing, image=f)

            # Check if owner needs to submit ID verification AFTER entering details!
            if request.user.verification_status != 'approved':
                if request.user.verification_status == 'pending':
                    messages.warning(
                        request,
                        'Room details & photos saved! Your ID proof is currently pending Admin review. Your room listing will be published live as soon as your ID is approved.'
                    )
                    return redirect('profile_settings')
                else:
                    messages.warning(
                        request,
                        'Room details & photos saved successfully! To publish your room live so guests can view and book it, please submit your Government ID document now.'
                    )
                    return redirect('submit_verification')

            messages.success(request, 'Your room has been published live successfully!')
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
        messages.success(request, f'OTP sent to {request.user.phone} via SMS ')
        channel = 'sms'
    else:
        # SMS failed — try email fallback
        email_ok, email_err = _send_email_otp(request.user, code)
        if email_ok and not dev_mode:
            messages.success(request, f'OTP sent to {request.user.email} via Email ')
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
# PHONE OTP LOGIN (no password needed)
# ─────────────────────────────────────────────────────────────

def phone_login_request(request):
    """Step 1: User enters phone number, we send OTP."""
    if request.method == 'POST':
        import re
        phone = request.POST.get('phone', '').strip()
        digits = re.sub(r'\D', '', phone)
        # Extract the last 10 digits to seamlessly handle +91, 91, 0, spaces, & mobile keyboard auto-fill
        if len(digits) >= 10:
            digits = digits[-10:]

        if len(digits) != 10:
            messages.error(request, 'Please enter a valid 10-digit mobile number.')
            return render(request, 'core/phone_login_request.html')

        # Rate limiting
        from django.core.cache import cache
        rate_key = f'phone_login_rate_{digits}'
        if cache.get(rate_key):
            messages.error(request, 'Please wait 60 seconds before requesting another OTP.')
            return render(request, 'core/phone_login_request.html')

        # Generate OTP
        code = f'{random.randint(0, 999999):06d}'

        # Store in session for verification
        request.session['phone_login_number'] = digits
        request.session['phone_login_code'] = code

        cache.set(rate_key, 1, timeout=60)

        # Send OTP via SMS
        from django.conf import settings as dj_settings
        dev_mode = getattr(dj_settings, 'OTP_DEV_MODE', True)
        dev_code = None

        sms_ok, sms_err = _send_sms_otp(digits, code)
        if sms_ok and not dev_mode:
            messages.success(request, f'OTP sent to +91 {digits} ')
        else:
            # In dev mode, show code on screen
            dev_code = code
            if dev_mode:
                messages.info(request, f'Dev mode: Your OTP is {code}')
            else:
                messages.warning(request, f'Could not send SMS. Your OTP is: {code}')
                dev_code = code

        return render(request, 'core/phone_login_verify.html', {
            'phone': digits,
            'dev_code': dev_code,
        })

    return render(request, 'core/phone_login_request.html')


def phone_login_verify(request):
    """Step 2: User enters OTP, we verify and log them in."""
    phone = request.session.get('phone_login_number')
    stored_code = request.session.get('phone_login_code')

    if not phone or not stored_code:
        messages.error(request, 'Session expired. Please request a new OTP.')
        return redirect('phone_login_request')

    if request.method == 'POST':
        entered = request.POST.get('code', '').strip()

        if entered != stored_code:
            # Track attempts
            from django.core.cache import cache
            key = f'phone_login_attempts_{phone}'
            attempts = cache.get(key, 0) + 1
            cache.set(key, attempts, timeout=600)
            if attempts >= 5:
                cache.delete(key)
                del request.session['phone_login_number']
                del request.session['phone_login_code']
                messages.error(request, 'Too many wrong attempts. Please request a new OTP.')
                return redirect('phone_login_request')
            messages.error(request, f'Incorrect code. {5 - attempts} attempt(s) left.')
            return render(request, 'core/phone_login_verify.html', {'phone': phone, 'dev_code': None})

        # OTP is correct — find or create user
        user = User.objects.filter(phone=phone).first()
        if not user:
            # Auto-create a new guest account
            import uuid
            short_id = uuid.uuid4().hex[:8]
            user = User.objects.create_user(
                username=f'user_{short_id}',
                password=None,  # No password — phone-only login
                phone=phone,
                phone_verified=True,
                role='guest',
            )
            user.set_unusable_password()
            user.save()
            messages.success(request, f'Welcome to SoloNest! Your account has been created.')
        else:
            user.phone_verified = True
            user.save()

        # Log the user in
        login(request, user, backend='django.contrib.auth.backends.ModelBackend')

        # Clean up session
        del request.session['phone_login_number']
        del request.session['phone_login_code']
        from django.core.cache import cache
        cache.delete(f'phone_login_attempts_{phone}')

        return redirect('home')

    return render(request, 'core/phone_login_verify.html', {'phone': phone, 'dev_code': None})


# ─────────────────────────────────────────────────────────────
# IDENTITY VERIFICATION
# ─────────────────────────────────────────────────────────────


@login_required
def submit_verification(request):
    if request.method == 'POST':
        f = request.FILES.get('id_proof')
        if not f:
            messages.error(request, 'Please select an ID proof document file to upload.')
            return render(request, 'core/submit_verification.html')

        allowed = ['image/jpeg', 'image/png', 'image/jpg', 'image/webp', 'application/pdf']
        if f.content_type.lower() not in allowed:
            messages.error(request, 'Invalid file format. Please upload a clear JPG, PNG, WEBP image, or PDF document.')
            return render(request, 'core/submit_verification.html')

        if f.size > 10 * 1024 * 1024:
            messages.error(request, 'File size too large. Maximum allowed document size is 10MB.')
            return render(request, 'core/submit_verification.html')

        request.user.id_proof = f
        request.user.verification_status = 'pending'
        request.user.save()
        messages.success(request, ' Your ID proof document has been submitted successfully! Our Admin team will review and approve it shortly.')
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
            messages.success(request, 'Payment successful! ')
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


# ─────────────────────────────────────────────────────────────
# REAL-TIME NOTIFICATION API FOR BROWSER PUSH ALERTS
# ─────────────────────────────────────────────────────────────

@login_required
def api_poll_notifications(request):
    """
    Polled by browser JavaScript to deliver instant real-time
    Web Browser Notifications to Room Owners when new bookings arrive!
    """
    notifs = Notification.objects.filter(user=request.user, is_read=False).order_by('-created_at')[:10]
    data = [
        {
            'id': n.id,
            'message': n.message,
            'link': n.link,
            'created_at': n.created_at.strftime('%I:%M %p, %d %b'),
        }
        for n in notifs
    ]
    return JsonResponse({
        'unread_count': len(data),
        'notifications': data
    })


@login_required
def api_mark_notification_read(request, pk):
    notif = get_object_or_404(Notification, pk=pk, user=request.user)
    notif.is_read = True
    notif.save()
    return JsonResponse({'success': True})


def service_worker(request):
    """Serve sw.js directly at /sw.js with Service-Worker-Allowed header to prevent 404s."""
    from django.conf import settings
    from django.http import HttpResponse
    sw_path = os.path.join(settings.BASE_DIR, 'static', 'js', 'sw.js')
    if os.path.exists(sw_path):
        with open(sw_path, 'r', encoding='utf-8') as f:
            content = f.read()
    else:
        content = "// Service worker"
    response = HttpResponse(content, content_type='application/javascript')
    response['Service-Worker-Allowed'] = '/'
    return response


def manifest_json(request):
    """Serve manifest.json directly at /manifest.json for Android PWA & Mobile Push."""
    from django.conf import settings
    from django.http import HttpResponse
    manifest_path = os.path.join(settings.BASE_DIR, 'static', 'manifest.json')
    if os.path.exists(manifest_path):
        with open(manifest_path, 'r', encoding='utf-8') as f:
            content = f.read()
    else:
        content = "{}"
    return HttpResponse(content, content_type='application/manifest+json')


# ─────────────────────────────────────────────────────────────
# REST API ENDPOINTS FOR FLUTTER MOBILE APP
# ─────────────────────────────────────────────────────────────

@csrf_exempt
def api_listings(request):
    """
    GET endpoint returning JSON list of all available listings with their first image URL.
    Supports query params: city, room_type.
    Return fields: id, title, city, area, room_type, room_type_display, price_per_day,
    price_per_month, wifi, ac, food_included, parking, is_verified, image_url, owner_name,
    gender_preference, stay_type.
    """
    if request.method != 'GET':
        return JsonResponse({'error': 'Method not allowed. Use GET.'}, status=405)

    try:
        listings = Listing.objects.filter(is_available=True).prefetch_related('images').select_related('owner')

        city = request.GET.get('city', '').strip()
        room_type = request.GET.get('room_type', '').strip()

        if city:
            listings = listings.filter(Q(city__icontains=city) | Q(area__icontains=city))
        if room_type:
            if room_type == 'hotel':
                listings = listings.filter(Q(room_type='hotel') | Q(room_type='private'))
            elif room_type == 'pg':
                listings = listings.filter(Q(room_type__startswith='pg_') | Q(room_type='pg') | Q(room_type='shared'))
            elif room_type == 'homestay':
                listings = listings.filter(Q(room_type__startswith='homestay_') | Q(room_type='homestay') | Q(room_type='guesthouse'))
            elif room_type == 'rental':
                listings = listings.filter(Q(room_type='rental') | Q(room_type='full_house'))
            else:
                listings = listings.filter(room_type=room_type)

        listings = listings.order_by('-is_verified', '-created_at')

        results = []
        for l in listings:
            first_img = l.images.first()
            img_url = request.build_absolute_uri(first_img.image.url) if first_img and first_img.image else None

            results.append({
                'id': l.id,
                'title': l.title,
                'city': l.city,
                'area': l.area,
                'room_type': l.room_type,
                'room_type_display': l.get_room_type_display(),
                'price_per_day': float(l.price_per_day) if l.price_per_day is not None else None,
                'price_per_month': float(l.price_per_month) if l.price_per_month is not None else None,
                'wifi': l.wifi,
                'ac': l.ac,
                'food_included': l.food_included,
                'parking': l.parking,
                'is_verified': l.is_verified,
                'image_url': img_url,
                'owner_name': l.owner.full_name,
                'gender_preference': l.gender_preference,
                'stay_type': l.stay_type,
            })

        return JsonResponse(results, safe=False)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
def api_listing_detail(request, pk):
    """
    GET endpoint returning full JSON detail of a single listing including ALL image URLs,
    owner info, amenities, description, address.
    """
    if request.method != 'GET':
        return JsonResponse({'error': 'Method not allowed. Use GET.'}, status=405)

    try:
        try:
            listing = Listing.objects.prefetch_related('images').select_related('owner').get(pk=pk)
        except Listing.DoesNotExist:
            return JsonResponse({'error': 'Listing not found.'}, status=404)

        images = [
            request.build_absolute_uri(img.image.url)
            for img in listing.images.all()
            if img.image
        ]

        data = {
            'id': listing.id,
            'title': listing.title,
            'description': listing.description,
            'city': listing.city,
            'area': listing.area,
            'address': listing.address,
            'room_type': listing.room_type,
            'room_type_display': listing.get_room_type_display(),
            'gender_preference': listing.gender_preference,
            'gender_preference_display': listing.get_gender_preference_display(),
            'stay_type': listing.stay_type,
            'stay_type_display': listing.get_stay_type_display(),
            'price_per_day': float(listing.price_per_day) if listing.price_per_day is not None else None,
            'price_per_month': float(listing.price_per_month) if listing.price_per_month is not None else None,
            'wifi': listing.wifi,
            'ac': listing.ac,
            'attached_bathroom': listing.attached_bathroom,
            'food_included': listing.food_included,
            'parking': listing.parking,
            'amenities': {
                'wifi': listing.wifi,
                'ac': listing.ac,
                'attached_bathroom': listing.attached_bathroom,
                'food_included': listing.food_included,
                'parking': listing.parking,
            },
            'is_available': listing.is_available,
            'is_verified': listing.is_verified,
            'latitude': listing.latitude,
            'longitude': listing.longitude,
            'views_count': listing.views_count,
            'average_rating': listing.average_rating(),
            'created_at': listing.created_at.isoformat() if listing.created_at else None,
            'images': images,
            'owner': {
                'id': listing.owner.id,
                'username': listing.owner.username,
                'full_name': listing.owner.full_name,
                'first_name': listing.owner.first_name,
                'last_name': listing.owner.last_name,
                'phone': listing.owner.phone,
                'gender': listing.owner.gender,
                'bio': listing.owner.bio,
                'is_verified': listing.owner.is_verified,
            },
        }
        return JsonResponse(data)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
def api_phone_login(request):
    """
    POST endpoint accepting {phone} in JSON body.
    Generate 6-digit OTP, store in session, return {success: true, message: 'OTP sent'}.
    Reuse the existing OTP logic pattern from phone_login_request view.
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Method not allowed. Use POST.'}, status=405)

    try:
        data = {}
        if request.body:
            try:
                data = json.loads(request.body.decode('utf-8'))
            except (json.JSONDecodeError, UnicodeDecodeError):
                data = {}

        phone = data.get('phone') or request.POST.get('phone', '')
        if not phone:
            return JsonResponse({'success': False, 'error': 'Phone number is required.'}, status=400)

        import re
        digits = re.sub(r'\D', '', str(phone).strip())
        if len(digits) >= 10:
            digits = digits[-10:]

        if len(digits) != 10:
            return JsonResponse({'success': False, 'error': 'Please enter a valid 10-digit mobile number.'}, status=400)

        # Rate limiting
        from django.core.cache import cache
        rate_key = f'phone_login_rate_{digits}'
        if cache.get(rate_key):
            return JsonResponse({'success': False, 'error': 'Please wait 60 seconds before requesting another OTP.'}, status=429)

        # Generate OTP
        code = f'{random.randint(0, 999999):06d}'

        # Store in session for verification
        request.session['phone_login_number'] = digits
        request.session['phone_login_code'] = code
        if not request.session.session_key:
            request.session.save()

        cache.set(rate_key, 1, timeout=60)

        # Send OTP via SMS
        from django.conf import settings as dj_settings
        dev_mode = getattr(dj_settings, 'OTP_DEV_MODE', True)

        sms_ok, sms_err = _send_sms_otp(digits, code)

        res = {
            'success': True,
            'message': 'OTP sent',
        }
        if dev_mode:
            res['dev_code'] = code

        return JsonResponse(res)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@csrf_exempt
def api_phone_verify(request):
    """
    POST endpoint accepting {phone, code} in JSON body.
    Verify OTP, create/find user, return {success: true, token: session_key, user: {id, username, phone, role}}.
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Method not allowed. Use POST.'}, status=405)

    try:
        data = {}
        if request.body:
            try:
                data = json.loads(request.body.decode('utf-8'))
            except (json.JSONDecodeError, UnicodeDecodeError):
                data = {}

        phone = data.get('phone') or request.POST.get('phone', '')
        entered_code = data.get('code') or request.POST.get('code', '')

        if not phone or not entered_code:
            return JsonResponse({'success': False, 'error': 'Both phone and code are required.'}, status=400)

        import re
        digits = re.sub(r'\D', '', str(phone).strip())
        if len(digits) >= 10:
            digits = digits[-10:]

        entered_code = str(entered_code).strip()

        stored_phone = request.session.get('phone_login_number')
        stored_code = request.session.get('phone_login_code')

        if not stored_phone or not stored_code:
            return JsonResponse({'success': False, 'error': 'Session expired or OTP not requested. Please request a new OTP.'}, status=400)

        if stored_phone != digits:
            return JsonResponse({'success': False, 'error': 'Phone number does not match OTP request.'}, status=400)

        if entered_code != stored_code:
            from django.core.cache import cache
            key = f'phone_login_attempts_{digits}'
            attempts = cache.get(key, 0) + 1
            cache.set(key, attempts, timeout=600)
            if attempts >= 5:
                cache.delete(key)
                request.session.pop('phone_login_number', None)
                request.session.pop('phone_login_code', None)
                return JsonResponse({'success': False, 'error': 'Too many wrong attempts. Please request a new OTP.'}, status=400)
            return JsonResponse({'success': False, 'error': f'Incorrect code. {5 - attempts} attempt(s) left.'}, status=400)

        # OTP is correct — find or create user
        user = User.objects.filter(phone=digits).first()
        if not user:
            import uuid
            short_id = uuid.uuid4().hex[:8]
            user = User.objects.create_user(
                username=f'user_{short_id}',
                password=None,
                phone=digits,
                phone_verified=True,
                role='guest',
            )
            user.set_unusable_password()
            user.save()
        else:
            user.phone_verified = True
            user.save()

        login(request, user, backend='django.contrib.auth.backends.ModelBackend')
        request.session.save()

        # Clean up session OTP keys
        request.session.pop('phone_login_number', None)
        request.session.pop('phone_login_code', None)
        from django.core.cache import cache
        cache.delete(f'phone_login_attempts_{digits}')

        return JsonResponse({
            'success': True,
            'token': request.session.session_key,
            'user': {
                'id': user.id,
                'username': user.username,
                'phone': user.phone,
                'role': user.role,
            }
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@csrf_exempt
def api_create_booking(request):
    """
    POST endpoint (login required via session) accepting {listing_id, check_in, check_out}.
    Create a Booking with status='requested'. Return {success: true, booking_id}.
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Method not allowed. Use POST.'}, status=405)

    try:
        user = request.user
        if not user.is_authenticated:
            session_key = (
                request.headers.get('x-session-id')
                or request.headers.get('session-key')
            )
            auth_header = request.headers.get('authorization', '')
            if not session_key and auth_header:
                if auth_header.startswith('Bearer ') or auth_header.startswith('Session '):
                    session_key = auth_header.split(' ', 1)[1].strip()
                elif ' ' not in auth_header:
                    session_key = auth_header.strip()

            if session_key:
                from django.contrib.sessions.models import Session
                try:
                    session = Session.objects.get(session_key=session_key)
                    session_data = session.get_decoded()
                    user_id = session_data.get('_auth_user_id')
                    if user_id:
                        user = User.objects.filter(pk=user_id).first()
                except Session.DoesNotExist:
                    pass

        if not user or not user.is_authenticated:
            return JsonResponse({'success': False, 'error': 'Authentication required. Please log in.'}, status=401)

        data = {}
        if request.body:
            try:
                data = json.loads(request.body.decode('utf-8'))
            except (json.JSONDecodeError, UnicodeDecodeError):
                data = {}

        listing_id = data.get('listing_id') or request.POST.get('listing_id')
        check_in_str = data.get('check_in') or request.POST.get('check_in')
        check_out_str = data.get('check_out') or request.POST.get('check_out')
        message = data.get('message') or request.POST.get('message', '')

        if not listing_id or not check_in_str or not check_out_str:
            return JsonResponse({'success': False, 'error': 'listing_id, check_in, and check_out are required.'}, status=400)

        try:
            listing = Listing.objects.get(pk=listing_id)
        except Listing.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Listing not found.'}, status=404)

        if not listing.is_available:
            return JsonResponse({'success': False, 'error': 'Sorry, this room is currently not available for booking.'}, status=400)

        if user == listing.owner:
            return JsonResponse({'success': False, 'error': 'You cannot book your own room.'}, status=400)

        from datetime import datetime
        try:
            if isinstance(check_in_str, str):
                check_in = datetime.strptime(check_in_str.strip(), '%Y-%m-%d').date()
            else:
                check_in = check_in_str
            if isinstance(check_out_str, str):
                check_out = datetime.strptime(check_out_str.strip(), '%Y-%m-%d').date()
            else:
                check_out = check_out_str
        except (ValueError, TypeError):
            return JsonResponse({'success': False, 'error': 'Invalid date format. Please use YYYY-MM-DD.'}, status=400)

        today = date.today()
        if check_in < today:
            return JsonResponse({'success': False, 'error': 'Check-in date cannot be in the past.'}, status=400)

        if check_out <= check_in:
            return JsonResponse({'success': False, 'error': 'Check-out must be after check-in.'}, status=400)

        overlap = Booking.objects.filter(
            listing=listing,
            status__in=['requested', 'approved'],
            check_in__lt=check_out,
            check_out__gt=check_in,
        ).exists()
        if overlap:
            return JsonResponse({'success': False, 'error': 'Those dates overlap with an existing booking for this room. Please choose different dates.'}, status=400)

        booking = Booking.objects.create(
            listing=listing,
            guest=user,
            check_in=check_in,
            check_out=check_out,
            message=message or '',
            status='requested',
        )

        notify(
            listing.owner,
            f'New booking request for "{listing.title}" from {user.username}.',
            f'/booking/{booking.pk}/'
        )

        return JsonResponse({
            'success': True,
            'booking_id': booking.id,
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

