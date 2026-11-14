from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from .models import User, Listing, ListingImage, Booking, Message, Review, Payment, Notification, Favorite, Report, OTPCode


# ─────────────────────────────────────────────────────────────
# ADMIN BRANDING
# ─────────────────────────────────────────────────────────────
admin.site.site_header = "SoloNest Administration"
admin.site.site_title = "SoloNest Admin Portal"
admin.site.index_title = "SoloNest Master Operations & Insights"


# ─────────────────────────────────────────────────────────────
# USER ADMIN
# ─────────────────────────────────────────────────────────────
class SoloNestUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ('SoloNest Customer Details', {
            'fields': ('role', 'phone', 'gender', 'age', 'from_location', 'bio', 'phone_verified')
        }),
        ('ID Verification & Documents', {
            'fields': ('id_proof', 'verification_status', 'is_verified')
        }),
    )
    list_display = ('username', 'full_name_display', 'role_badge', 'phone', 'verification_badge', 'id_proof_preview', 'phone_verified_badge', 'date_joined')
    list_filter = ('role', 'verification_status', 'is_verified', 'phone_verified', 'gender')
    search_fields = ('username', 'email', 'first_name', 'last_name', 'phone', 'from_location')
    actions = ['approve_identity', 'reject_identity']
    ordering = ('-date_joined',)

    def full_name_display(self, obj):
        name = obj.full_name or obj.username
        email = f"<br><span style='color:#6B7280;font-size:11px;'>{obj.email}</span>" if obj.email else ""
        return format_html(f"<strong>{name}</strong>{email}")
    full_name_display.short_description = "User / Email"

    def role_badge(self, obj):
        if obj.role == 'owner':
            return format_html('<span style="background:#EEF2FF;color:#4F46E5;border:1px solid #C7D2FE;padding:3px 9px;border-radius:12px;font-weight:700;font-size:11px;">🏠 Owner</span>')
        return format_html('<span style="background:#F0FDF4;color:#16A34A;border:1px solid #BBF7D0;padding:3px 9px;border-radius:12px;font-weight:700;font-size:11px;">🎒 Guest</span>')
    role_badge.short_description = "Role"

    def verification_badge(self, obj):
        if obj.verification_status == 'approved' or obj.is_verified:
            return format_html('<span style="background:#DCFCE7;color:#15803D;border:1px solid #86EFAC;padding:3px 9px;border-radius:12px;font-weight:700;font-size:11px;">✓ Verified</span>')
        elif obj.verification_status == 'rejected':
            return format_html('<span style="background:#FEE2E2;color:#DC2626;border:1px solid #FCA5A5;padding:3px 9px;border-radius:12px;font-weight:700;font-size:11px;">✕ Rejected</span>')
        elif obj.verification_status == 'pending':
            return format_html('<span style="background:#FEF3C7;color:#D97706;border:1px solid #FCD34D;padding:3px 9px;border-radius:12px;font-weight:700;font-size:11px;">⏳ Pending</span>')
        return format_html('<span style="color:#9CA3AF;font-size:11px;">Unsubmitted</span>')
    verification_badge.short_description = "ID Status"

    def phone_verified_badge(self, obj):
        if obj.phone_verified:
            return format_html('<span style="color:#16A34A;font-weight:700;font-size:11px;">✓ Yes</span>')
        return format_html('<span style="color:#9CA3AF;font-size:11px;">No</span>')
    phone_verified_badge.short_description = "Phone Ver."

    def id_proof_preview(self, obj):
        if obj.id_proof:
            return format_html('<a href="{}" target="_blank" style="font-weight:700;color:#4F46E5;background:#EEF2FF;border:1px solid #C7D2FE;padding:4px 10px;border-radius:6px;text-decoration:none;font-size:11px;">📄 View ID</a>', obj.id_proof.url)
        return format_html('<span style="color:#9CA3AF;font-size:11px;">—</span>')
    id_proof_preview.short_description = "ID Document"

    def approve_identity(self, request, queryset):
        count = 0
        for user in queryset:
            user.is_verified = True
            user.verification_status = 'approved'
            user.save()
            Listing.objects.filter(owner=user).update(is_verified=True)
            count += 1
            Notification.objects.create(
                user=user,
                message='ID Verification Approved: Your owner ID proof document has been verified and approved by Admin. Your saved room listings are now published live!',
                link='/dashboard/'
            )
        self.message_user(request, f"Approved ID verification for {count} user(s).")
    approve_identity.short_description = "✓ Approve selected owners' ID verification"

    def reject_identity(self, request, queryset):
        count = 0
        for user in queryset:
            user.is_verified = False
            user.verification_status = 'rejected'
            user.save()
            count += 1
            Notification.objects.create(
                user=user,
                message='ID Verification Update: Your ID proof document could not be verified. Please re-upload a clear ID document in Profile Settings.',
                link='/settings/verify-id/'
            )
        self.message_user(request, f"Rejected ID verification for {count} user(s).")
    reject_identity.short_description = "✕ Reject selected owners' ID verification"


# ─────────────────────────────────────────────────────────────
# LISTINGS ADMIN
# ─────────────────────────────────────────────────────────────
class ListingImageInline(admin.TabularInline):
    model = ListingImage
    extra = 1
    readonly_fields = ('image_preview',)

    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="width:70px;height:50px;object-fit:cover;border-radius:6px;border:1px solid #E5E7EB;" />', obj.image.url)
        return ""
    image_preview.short_description = "Preview"


@admin.register(Listing)
class ListingAdmin(admin.ModelAdmin):
    list_display = ('thumbnail_preview', 'title_display', 'owner', 'location_display', 'pricing_display', 'status_badge', 'is_verified_badge', 'views_count')
    list_filter = ('city', 'room_type', 'gender_preference', 'is_available', 'is_verified')
    search_fields = ('title', 'city', 'area', 'address', 'owner__username', 'owner__email')
    inlines = [ListingImageInline]
    actions = ['mark_verified', 'deactivate_listing', 'activate_listing']
    list_per_page = 20

    def thumbnail_preview(self, obj):
        first_img = obj.images.first()
        if first_img and first_img.image:
            return format_html('<img src="{}" style="width:56px;height:42px;object-fit:cover;border-radius:6px;border:1px solid #E5E7EB;box-shadow:0 1px 3px rgba(0,0,0,0.1);" />', first_img.image.url)
        return format_html('<div style="width:56px;height:42px;background:#F3F4F6;border-radius:6px;display:flex;align-items:center;justify-content:center;color:#9CA3AF;font-size:10px;font-weight:600;">No photo</div>')
    thumbnail_preview.short_description = "Photo"

    def title_display(self, obj):
        rtype = f"<span style='color:#6B7280;font-size:11px;'>{obj.get_room_type_display()}</span>"
        return format_html(f"<strong>{obj.title}</strong><br>{rtype}")
    title_display.short_description = "Listing Title"

    def location_display(self, obj):
        area = f"{obj.area}, " if obj.area else ""
        return format_html(f"📍 <strong>{obj.city}</strong><br><span style='color:#6B7280;font-size:11px;'>{area}</span>")
    location_display.short_description = "Location"

    def pricing_display(self, obj):
        parts = []
        if obj.price_per_day:
            parts.append(f"<span style='color:#16A34A;font-weight:700;'>₹{obj.price_per_day}</span>/day")
        if obj.price_per_month:
            parts.append(f"<span style='color:#4F46E5;font-weight:700;'>₹{obj.price_per_month}</span>/mo")
        return format_html("<br>".join(parts) if parts else "—")
    pricing_display.short_description = "Pricing"

    def status_badge(self, obj):
        if obj.is_available:
            return format_html('<span style="background:#DCFCE7;color:#15803D;padding:3px 8px;border-radius:12px;font-weight:700;font-size:11px;">Active</span>')
        return format_html('<span style="background:#F3F4F6;color:#6B7280;padding:3px 8px;border-radius:12px;font-weight:600;font-size:11px;">Inactive</span>')
    status_badge.short_description = "Availability"

    def is_verified_badge(self, obj):
        if obj.is_verified:
            return format_html('<span style="color:#16A34A;font-weight:700;font-size:11px;">✓ Verified</span>')
        return format_html('<span style="color:#9CA3AF;font-size:11px;">Unverified</span>')
    is_verified_badge.short_description = "Verification"

    def mark_verified(self, request, queryset):
        queryset.update(is_verified=True)
    mark_verified.short_description = "✓ Mark selected listings as Verified"

    def deactivate_listing(self, request, queryset):
        queryset.update(is_available=False)
    deactivate_listing.short_description = "✕ Deactivate selected listings"

    def activate_listing(self, request, queryset):
        queryset.update(is_available=True)
    activate_listing.short_description = "✓ Activate selected listings"


# ─────────────────────────────────────────────────────────────
# BOOKINGS ADMIN
# ─────────────────────────────────────────────────────────────
@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('id', 'listing_title', 'guest_info', 'dates_display', 'status_badge', 'payment_badge', 'created_at')
    list_filter = ('status', 'is_paid')
    search_fields = ('listing__title', 'guest__username', 'guest__phone', 'guest__email')
    ordering = ('-created_at',)

    def listing_title(self, obj):
        return format_html(f"<strong>{obj.listing.title}</strong><br><span style='color:#6B7280;font-size:11px;'>📍 {obj.listing.city}</span>")
    listing_title.short_description = "Listing"

    def guest_info(self, obj):
        phone = f"<br><span style='color:#6B7280;font-size:11px;'>📞 {obj.guest.phone}</span>" if obj.guest.phone else ""
        return format_html(f"<strong>{obj.guest.full_name or obj.guest.username}</strong>{phone}")
    guest_info.short_description = "Guest"

    def dates_display(self, obj):
        return format_html(f"📅 <strong>{obj.check_in}</strong> → <strong>{obj.check_out}</strong>")
    dates_display.short_description = "Stay Dates"

    def status_badge(self, obj):
        styles = {
            'pending': ('#FEF3C7', '#D97706', '⏳ Pending'),
            'approved': ('#DCFCE7', '#15803D', '✓ Approved'),
            'rejected': ('#FEE2E2', '#DC2626', '✕ Rejected'),
            'cancelled': ('#F3F4F6', '#6B7280', 'Cancelled'),
            'completed': ('#E0E7FF', '#4338CA', '🎉 Completed'),
        }
        bg, col, text = styles.get(obj.status, ('#F3F4F6', '#6B7280', obj.status.title()))
        return format_html(f'<span style="background:{bg};color:{col};padding:3px 9px;border-radius:12px;font-weight:700;font-size:11px;">{text}</span>')
    status_badge.short_description = "Status"

    def payment_badge(self, obj):
        if obj.is_paid:
            return format_html('<span style="color:#16A34A;font-weight:700;font-size:11px;">✓ Paid</span>')
        return format_html('<span style="color:#D97706;font-size:11px;">Pay at Property</span>')
    payment_badge.short_description = "Payment"


# ─────────────────────────────────────────────────────────────
# PAYMENTS ADMIN
# ─────────────────────────────────────────────────────────────
@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('id', 'booking_ref', 'amount_display', 'status_badge', 'payment_id', 'created_at')
    list_filter = ('status',)
    search_fields = ('razorpay_payment_id', 'booking__listing__title', 'booking__guest__username')

    def booking_ref(self, obj):
        return format_html(f"Booking #{obj.booking.id} — {obj.booking.listing.title}")
    booking_ref.short_description = "Booking"

    def amount_display(self, obj):
        return format_html(f"<strong style='color:#16A34A;font-size:13px;'>₹{obj.amount}</strong>")
    amount_display.short_description = "Amount"

    def status_badge(self, obj):
        if obj.status == 'completed':
            return format_html('<span style="background:#DCFCE7;color:#15803D;padding:3px 8px;border-radius:12px;font-weight:700;font-size:11px;">Completed</span>')
        elif obj.status == 'failed':
            return format_html('<span style="background:#FEE2E2;color:#DC2626;padding:3px 8px;border-radius:12px;font-weight:700;font-size:11px;">Failed</span>')
        return format_html('<span style="background:#FEF3C7;color:#D97706;padding:3px 8px;border-radius:12px;font-weight:700;font-size:11px;">Pending</span>')
    status_badge.short_description = "Payment Status"

    def payment_id(self, obj):
        return obj.razorpay_payment_id or "—"
    payment_id.short_description = "Transaction ID"


# ─────────────────────────────────────────────────────────────
# REPORTS ADMIN
# ─────────────────────────────────────────────────────────────
@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ('listing', 'reporter', 'reason', 'status_badge', 'created_at')
    list_filter = ('reason', 'status')
    actions = ['mark_reviewed', 'mark_dismissed', 'deactivate_reported_listing']

    def status_badge(self, obj):
        if obj.status == 'reviewed':
            return format_html('<span style="background:#DCFCE7;color:#15803D;padding:3px 8px;border-radius:12px;font-weight:700;font-size:11px;">Reviewed</span>')
        elif obj.status == 'dismissed':
            return format_html('<span style="background:#F3F4F6;color:#6B7280;padding:3px 8px;border-radius:12px;font-weight:600;font-size:11px;">Dismissed</span>')
        return format_html('<span style="background:#FEF3C7;color:#D97706;padding:3px 8px;border-radius:12px;font-weight:700;font-size:11px;">Pending</span>')
    status_badge.short_description = "Status"

    def mark_reviewed(self, request, queryset):
        queryset.update(status='reviewed')
    mark_reviewed.short_description = "✓ Mark selected reports as Reviewed"

    def mark_dismissed(self, request, queryset):
        queryset.update(status='dismissed')
    mark_dismissed.short_description = "✕ Dismiss selected reports"

    def deactivate_reported_listing(self, request, queryset):
        listing_ids = queryset.values_list('listing_id', flat=True)
        Listing.objects.filter(pk__in=listing_ids).update(is_available=False)
        queryset.update(status='reviewed')
    deactivate_reported_listing.short_description = "⛔ Deactivate the reported listing(s)"


# ─────────────────────────────────────────────────────────────
# OTHER MODELS
# ─────────────────────────────────────────────────────────────
admin.site.register(User, SoloNestUserAdmin)
admin.site.register(Message)
admin.site.register(Review)
admin.site.register(Notification)
admin.site.register(Favorite)
admin.site.register(OTPCode)

