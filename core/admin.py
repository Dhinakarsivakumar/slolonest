from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Listing, ListingImage, Booking, Message, Review, Payment, Notification, Favorite, Report, OTPCode


class SoloNestUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ('SoloNest Info', {'fields': ('role', 'phone', 'phone_verified', 'id_proof', 'verification_status', 'is_verified')}),
    )
    list_display = ('username', 'email', 'role', 'verification_status', 'is_verified', 'phone_verified', 'is_staff')
    list_filter = ('role', 'is_verified', 'verification_status', 'phone_verified')
    actions = ['approve_identity', 'reject_identity']

    def approve_identity(self, request, queryset):
        queryset.update(is_verified=True, verification_status='approved')
    approve_identity.short_description = "Approve selected owners' ID verification"

    def reject_identity(self, request, queryset):
        queryset.update(is_verified=False, verification_status='rejected')
    reject_identity.short_description = "Reject selected owners' ID verification"


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
