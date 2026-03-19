from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Count
from django.utils import timezone
from events.models import Event, Registration

# Protect this view so only Library Staff and Superusers can see it
@staff_member_required(login_url='/admin/login/')
def dashboard(request):
    today = timezone.now().date()

    # 1. High-level Statistics
    total_events = Event.objects.count()
    total_registrations = Registration.objects.count()
    upcoming_events_count = Event.objects.filter(date__gte=today).count()

    # 2. Most Popular Upcoming Events
    # We use .annotate() to count registrations for each event directly in the database, 
    # and then order them from highest to lowest.
    popular_events = Event.objects.filter(date__gte=today).annotate(
        reg_count=Count('registrations')
    ).order_by('-reg_count')[:5] # Grab the top 5

    context = {
        'total_events': total_events,
        'total_registrations': total_registrations,
        'upcoming_events_count': upcoming_events_count,
        'popular_events': popular_events,
    }
    return render(request, 'analytics/dashboard.html', context)