from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User, Listing, ListingImage, Booking, Message, Review, Report


class SignUpForm(UserCreationForm):
    class Meta:
        model = User
        fields = ('username', 'email', 'phone', 'role', 'password1', 'password2')


class ListingForm(forms.ModelForm):
    class Meta:
        model = Listing
        # views_count is auto-managed, never shown to users
        exclude = ('owner', 'is_verified', 'created_at', 'views_count')
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Describe your room — size, floor, nearby places, house rules...'}),
            'address':     forms.TextInput(attrs={'placeholder': 'e.g. 12, 3rd Cross Street, Gandhi Nagar'}),
            'area':        forms.TextInput(attrs={'placeholder': 'e.g. Anna Nagar, Koramangala'}),
            'city':        forms.TextInput(attrs={'placeholder': 'e.g. Chennai, Bangalore, Mumbai'}),
            'price_per_day':   forms.NumberInput(attrs={'placeholder': '0.00', 'min': '0'}),
            'price_per_month': forms.NumberInput(attrs={'placeholder': '0.00', 'min': '0'}),
            'latitude':  forms.NumberInput(attrs={'placeholder': 'e.g. 13.0827', 'step': 'any'}),
            'longitude': forms.NumberInput(attrs={'placeholder': 'e.g. 80.2707', 'step': 'any'}),
        }


class BookingForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = ('check_in', 'check_out', 'message')
        widgets = {
            'check_in': forms.DateInput(attrs={'type': 'date'}),
            'check_out': forms.DateInput(attrs={'type': 'date'}),
            'message': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Tell the owner a bit about yourself (e.g. student, interview candidate, work purpose)...'}),
        }


class MessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ('text',)
        widgets = {
            'text': forms.TextInput(attrs={'placeholder': 'Type a message...'}),
        }


class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ('rating', 'comment')
        widgets = {
            'rating': forms.Select(choices=[(i, i) for i in range(1, 6)]),
            'comment': forms.Textarea(attrs={'rows': 3}),
        }


class ReportForm(forms.ModelForm):
    class Meta:
        model = Report
        fields = ('reason', 'details')
        widgets = {
            'details': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Add any details that will help us review this...'}),
        }
