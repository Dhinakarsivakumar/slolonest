from django.db import models
from django.conf import settings

User = settings.AUTH_USER_MODEL


class SupportTicket(models.Model):
    STATUS_CHOICES = [
        ('open',        'Open'),
        ('in_progress', 'In Progress'),
        ('resolved',    'Resolved'),
        ('closed',      'Closed'),
    ]
    PRIORITY_CHOICES = [
        ('low',    'Low'),
        ('medium', 'Medium'),
        ('high',   'High'),
        ('urgent', 'Urgent'),
    ]
    CATEGORY_CHOICES = [
        ('booking',   'Booking Issue'),
        ('payment',   'Payment Issue'),
        ('listing',   'Listing Issue'),
        ('account',   'Account Issue'),
        ('other',     'Other'),
    ]

    user        = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tickets')
    subject     = models.CharField(max_length=200)
    message     = models.TextField()
    category    = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='other')
    status      = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    priority    = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    assigned_to = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name='assigned_tickets')
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'#{self.pk} — {self.subject}'

    @property
    def reply_count(self):
        return self.replies.count()


class TicketReply(models.Model):
    ticket     = models.ForeignKey(SupportTicket, on_delete=models.CASCADE, related_name='replies')
    author     = models.ForeignKey(User, on_delete=models.CASCADE)
    message    = models.TextField()
    is_staff   = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f'Reply by {self.author.username} on #{self.ticket.pk}'
