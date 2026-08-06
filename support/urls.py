from django.urls import path
from . import views

urlpatterns = [
    # ── Portal Auth ──────────────────────────────────────────────
    path('login/',   views.portal_login,  name='portal_login'),
    path('logout/',  views.portal_logout, name='portal_logout'),

    # ── User-facing ─────────────────────────────────────────────
    path('contact/',             views.submit_ticket,      name='submit_ticket'),
    path('my-tickets/',          views.my_tickets,         name='my_tickets'),
    path('my-tickets/<int:pk>/', views.ticket_detail_user, name='ticket_detail_user'),

    # ── Staff Portal ─────────────────────────────────────────────
    path('portal/',                  views.portal_dashboard,     name='portal_dashboard'),
    path('portal/tickets/',          views.portal_tickets,       name='portal_tickets'),
    path('portal/tickets/<int:pk>/', views.portal_ticket_detail, name='portal_ticket_detail'),
    path('portal/users/',            views.portal_users,         name='portal_users'),
    path('portal/users/<int:pk>/',   views.portal_user_detail,   name='portal_user_detail'),
    path('portal/reports/',          views.portal_reports,       name='portal_reports'),
]
