from django.urls import path
from django.contrib.auth.views import LoginView, LogoutView
from . import views

urlpatterns = [
    # ── Public ──────────────────────────────────────────────
    path('',        views.home,      name='home'),
    path('help/',   views.help_page, name='help'),
    path('terms/',  views.terms_page, name='terms'),
    path('test-oauth/', views.test_oauth, name='test_oauth'),
    path('api/cities/', views.city_suggestions, name='city_suggestions'),



    # ── Auth ────────────────────────────────────────────────
    path('signup/',  views.signup,                                                   name='signup'),
    path('login/',   LoginView.as_view(template_name='core/login.html'),            name='login'),
    path('logout/',  LogoutView.as_view(),                                           name='logout'),
    path('welcome/', views.post_login_redirect,                                      name='post_login_redirect'),
    path('login/phone/',        views.phone_login_request,  name='phone_login_request'),
    path('login/phone/verify/', views.phone_login_verify,   name='phone_login_verify'),
    path('switch-mode/',        views.switch_mode,          name='switch_mode'),



    # ── Account / Settings ──────────────────────────────────
    path('settings/profile/',    views.profile_settings,   name='profile_settings'),
    path('settings/verify-id/',  views.submit_verification, name='submit_verification'),
    path('settings/send-otp/',   views.send_otp,           name='send_otp'),
    path('settings/verify-otp/', views.verify_otp,         name='verify_otp'),

    # ── Dashboard ───────────────────────────────────────────
    path('dashboard/', views.dashboard, name='dashboard'),

    # ── Listings ────────────────────────────────────────────
    path('list-room/',                views.add_listing,       name='add_listing'),
    path('listing/<int:pk>/',         views.listing_detail,    name='listing_detail'),
    path('listing/<int:pk>/edit/',    views.edit_listing,      name='edit_listing'),
    path('listing/<int:pk>/delete/',  views.delete_listing,    name='delete_listing'),
    path('listing/<int:pk>/favorite/',views.toggle_favorite,   name='toggle_favorite'),
    path('listing/<int:pk>/report/',  views.report_listing,    name='report_listing'),
    path('listing/<int:pk>/book/',    views.request_booking,   name='request_booking'),

    # ── Bookings ────────────────────────────────────────────
    path('booking/<int:pk>/',              views.booking_detail,   name='booking_detail'),
    path('booking/<int:pk>/cancel/',       views.cancel_booking,   name='cancel_booking'),
    path('booking/<int:pk>/review/',       views.add_review,       name='add_review'),
    path('booking/<int:pk>/pay/',          views.create_payment,   name='create_payment'),
    path('booking/<int:pk>/pay/callback/', views.payment_callback, name='payment_callback'),

    # ── Extras & APIs ───────────────────────────────────────
    path('favorites/',       views.favorites_list,     name='favorites_list'),
    path('notifications/',   views.notifications_list, name='notifications_list'),
    path('api/notifications/poll/', views.api_poll_notifications, name='api_poll_notifications'),
    path('api/notifications/<int:pk>/read/', views.api_mark_notification_read, name='api_mark_notification_read'),
    path('analytics/',       views.owner_analytics,    name='owner_analytics'),
    path('admin-analytics/', views.platform_analytics, name='platform_analytics'),
]
