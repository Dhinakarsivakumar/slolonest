from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Listing, ListingImage, Booking, Message, Review, Payment, Notification, Favorite, Report, OTPCode


from django.utils.html import format_html


class SoloNestUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ('SoloNest Customer Details', {
            'fields': ('role', 'phone', 'gender', 'age', 'from_location', 'bio', 'phone_verified')
        }),
        ('ID Verification & Documents', {
            'fields': ('id_proof', 'verification_status', 'is_verified')
        }),
    )
    list_display = ('username', 'full_name_display', 'role', 'phone', 'gender', 'from_location', 'id_proof_preview', 'verification_status', 'is_verified', 'phone_verified')
    list_filter = ('role', 'verification_status', 'is_verified', 'phone_verified', 'gender')
    search_fields = ('username', 'email', 'first_name', 'last_name', 'phone', 'from_location')
    actions = ['approve_identity', 'reject_identity']

    def full_name_display(self, obj):
        return obj.full_name
    full_name_display.short_description = "Full Name"

    def id_proof_preview(self, obj):
        if obj.id_proof:
            return format_html('<a href="{}" target="_blank" style="font-weight:700;color:#4F46E5;background:#EEF2FF;padding:4px 10px;border-radius:6px;text-decoration:none;">📄 View Document</a>', obj.id_proof.url)
        return format_html('<span style="color:#9CA3AF;">No Document</span>')
    id_proof_preview.short_description = "ID Document"

    def approve_identity(self, request, queryset):
        count = 0
        for user in queryset:
            user.is_verified = True
            user.verification_status = 'approved'
            user.save()
            count += 1
            Notification.objects.create(
                user=user,
                title='ID Verification Approved ✅',
                message='Your owner ID proof document has been verified and approved by Admin. You can now post room listings!'
            )
        self.message_user(request, f"Approved ID verification for {count} user(s).")
    approve_identity.short_description = "✅ Approve selected owners' ID verification"

    def reject_identity(self, request, queryset):
        count = 0
        for user in queryset:
            user.is_verified = False
            user.verification_status = 'rejected'
            user.save()
            count += 1
            Notification.objects.create(
                user=user,
                title='ID Verification Update ❌',
                message='Your ID proof document could not be verified. Please re-upload a clear ID document in Profile Settings.'
            )
        self.message_user(request, f"Rejected ID verification for {count} user(s).")
    reject_identity.short_description = "❌ Reject selected owners' ID verification"



class ListingImageInline(admin.TabularInline):
    model = ListingImage
    extra = 1


@admin.register(Listing)
class ListingAdmin(admin.ModelAdmin):
    list_display = ('title', 'owner', 'city', 'room_type', 'price_per_day', 'price_per_month', 'views_count', 'is_available', 'is_verified')
    list_filter = ('city', 'room_type', 'gender_preference', 'is_available', 'is_verified')
    search_fields = ('title', 'city', 'area', 'address')
    inlines = [ListingImageInline]
    actions = ['mark_verified', 'deactivate_listing']

    def mark_verified(self, request, queryset):
        queryset.update(is_verified=True)
    mark_verified.short_description = "Mark selected listings as Verified"

    def deactivate_listing(self, request, queryset):
        queryset.update(is_available=False)
    deactivate_listing.short_description = "Deactivate selected listings (hide from search)"


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('listing', 'guest', 'check_in', 'check_out', 'status', 'is_paid', 'created_at')
    list_filter = ('status', 'is_paid')


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ('listing', 'reporter', 'reason', 'status', 'created_at')
    list_filter = ('reason', 'status')
    actions = ['mark_reviewed', 'mark_dismissed', 'deactivate_reported_listing']

    def mark_reviewed(self, request, queryset):
        queryset.update(status='reviewed')
    mark_reviewed.short_description = "Mark selected reports as Reviewed"

    def mark_dismissed(self, request, queryset):
        queryset.update(status='dismissed')
    mark_dismissed.short_description = "Dismiss selected reports"

    def deactivate_reported_listing(self, request, queryset):
        listing_ids = queryset.values_list('listing_id', flat=True)
        Listing.objects.filter(pk__in=listing_ids).update(is_available=False)
        queryset.update(status='reviewed')
    deactivate_reported_listing.short_description = "Deactivate the reported listing(s)"


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('booking', 'amount', 'status', 'created_at')
    list_filter = ('status',)


admin.site.register(User, SoloNestUserAdmin)
admin.site.register(Message)
admin.site.register(Review)
admin.site.register(Notification)
admin.site.register(Favorite)
admin.site.register(OTPCode)
