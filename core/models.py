from django.contrib.auth.models import AbstractUser
from django.db import models
from django.urls import reverse


class User(AbstractUser):
    ROLE_CHOICES = [
        ('guest', 'Guest (looking for a room)'),
        ('owner', 'Owner (listing a room)'),
    ]
    GENDER_CHOICES = [
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
        ('prefer_not_to_say', 'Prefer not to say'),
    ]
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='guest')
    phone = models.CharField(max_length=15, blank=True)
    gender = models.CharField(max_length=20, choices=GENDER_CHOICES, blank=True)
    age = models.PositiveIntegerField(null=True, blank=True)
    from_location = models.CharField(max_length=100, blank=True, verbose_name="From (City/Hometown)")
    bio = models.TextField(blank=True, max_length=500)
    id_proof = models.FileField(upload_to='id_proofs/', blank=True, null=True)
    is_verified = models.BooleanField(default=False)
    phone_verified = models.BooleanField(default=False)
    VERIFICATION_STATUS_CHOICES = [
        ('not_submitted', 'Not submitted'),
        ('pending', 'Pending review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    verification_status = models.CharField(max_length=15, choices=VERIFICATION_STATUS_CHOICES, default='not_submitted')

    @property
    def full_name(self):
        name = f"{self.first_name} {self.last_name}".strip()
        return name if name else self.username

    def __str__(self):
        return f"{self.full_name} ({self.get_role_display()})"



class Listing(models.Model):
    ROOM_TYPE_CHOICES = [
        ('hotel', 'Hotel'),
        ('pg_private', 'PG - Private Room'),
        ('pg_shared', 'PG - Shared Room'),
        ('homestay_private', 'Home stay - Private Room'),
        ('homestay_shared', 'Home stay - Shared Room'),
        ('rental', 'Rental House'),
        ('private', 'Private Room'),
        ('shared', 'Shared Room'),
        ('guesthouse', 'Guest House'),
        ('full_house', 'Full Rental House'),
    ]
    GENDER_CHOICES = [
        ('any', 'Any'),
        ('male', 'Male Only'),
        ('female', 'Female Only'),
    ]
    STAY_CHOICES = [
        ('short', 'Short Stay (days)'),
        ('monthly', 'Monthly Stay'),
        ('both', 'Both'),
    ]

    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='listings')
    title = models.CharField(max_length=120)
    description = models.TextField()
    city = models.CharField(max_length=80)
    area = models.CharField(max_length=120, blank=True)
    address = models.CharField(max_length=255)

    room_type = models.CharField(max_length=30, choices=ROOM_TYPE_CHOICES, default='hotel')
    gender_preference = models.CharField(max_length=10, choices=GENDER_CHOICES, default='any')
    stay_type = models.CharField(max_length=10, choices=STAY_CHOICES, default='both')

    price_per_day = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    price_per_month = models.DecimalField(max_digits=9, decimal_places=2, null=True, blank=True)

    wifi = models.BooleanField(default=False)
    ac = models.BooleanField(default=False)
    attached_bathroom = models.BooleanField(default=False)
    food_included = models.BooleanField(default=False)
    parking = models.BooleanField(default=False)

    is_available = models.BooleanField(default=True)
    is_verified = models.BooleanField(default=False)
    latitude = models.FloatField(null=True, blank=True, help_text="e.g. 10.7870 (right-click the spot on Google Maps to copy)")
    longitude = models.FloatField(null=True, blank=True, help_text="e.g. 79.1378")
    views_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} - {self.city}"

    def get_absolute_url(self):
        return reverse('listing_detail', args=[self.pk])

    def average_rating(self):
        reviews = Review.objects.filter(booking__listing=self, review_type='guest_to_owner')
        if not reviews:
            return None
        return round(sum(r.rating for r in reviews) / reviews.count(), 1)


class ListingImage(models.Model):
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='listing_photos/')

    def __str__(self):
        return f"Image for {self.listing.title}"


class Booking(models.Model):
    STATUS_CHOICES = [
        ('requested', 'Requested'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('cancelled', 'Cancelled'),
        ('completed', 'Completed'),
    ]

    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name='bookings')
    guest = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bookings_made')
    check_in = models.DateField()
    check_out = models.DateField()
    message = models.TextField(blank=True)
    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default='requested')
    is_paid = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.guest.username} -> {self.listing.title} ({self.status})"


class Message(models.Model):
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.TextField()
    sent_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['sent_at']


class Review(models.Model):
    REVIEW_TYPE_CHOICES = [
        ('guest_to_owner', 'Guest reviewing Owner/Room'),
        ('owner_to_guest', 'Owner reviewing Guest'),
    ]
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='reviews')
    reviewer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews_given')
    review_type = models.CharField(max_length=20, choices=REVIEW_TYPE_CHOICES)
    rating = models.PositiveSmallIntegerField()
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('booking', 'review_type')


# ================= New feature models =================

class OTPCode(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='otp_codes')
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    is_used = models.BooleanField(default=False)

    def is_expired(self):
        from django.utils import timezone
        from datetime import timedelta
        return timezone.now() > self.created_at + timedelta(minutes=10)


class Payment(models.Model):
    STATUS_CHOICES = [
        ('created', 'Created'),
        ('paid', 'Paid'),
        ('failed', 'Failed'),
    ]
    booking = models.OneToOneField(Booking, on_delete=models.CASCADE, related_name='payment')
    razorpay_order_id = models.CharField(max_length=100, blank=True)
    razorpay_payment_id = models.CharField(max_length=100, blank=True)
    razorpay_signature = models.CharField(max_length=255, blank=True)
    amount = models.DecimalField(max_digits=9, decimal_places=2)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='created')
    created_at = models.DateTimeField(auto_now_add=True)


class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    message = models.CharField(max_length=255)
    link = models.CharField(max_length=255, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']


class Favorite(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favorites')
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name='favorited_by')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'listing')


class Report(models.Model):
    REASON_CHOICES = [
        ('fake', 'Fake / misleading listing'),
        ('unsafe', 'Unsafe or unhygienic'),
        ('scam', 'Suspected scam'),
        ('inappropriate', 'Inappropriate content'),
        ('other', 'Other'),
    ]
    STATUS_CHOICES = [
        ('open', 'Open'),
        ('reviewed', 'Reviewed'),
        ('dismissed', 'Dismissed'),
    ]
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name='reports')
    reporter = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reports_filed')
    reason = models.CharField(max_length=20, choices=REASON_CHOICES)
    details = models.TextField(blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='open')
    created_at = models.DateTimeField(auto_now_add=True)
