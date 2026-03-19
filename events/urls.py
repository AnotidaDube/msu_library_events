from django.urls import path
from . import views

app_name = 'events'

urlpatterns = [
    # The empty string '' means this is the main page for events
    path('', views.event_list, name='list'),
    
    # 1. STATIC PATHS (Must go before dynamic slug paths)
    path('calendar/', views.calendar_view, name='calendar'),
    path('api/calendar-data/', views.calendar_api, name='calendar_api'),
    path('series-poster/', views.generate_monthly_series_poster, name='series_poster'),
    
    # 2. DYNAMIC SLUG PATHS (Must go at the bottom)
    # We will use the event's slug to create a unique URL for each event detail page
    path('<slug:slug>/', views.event_detail, name='detail'),
    
    # Registration URL for events, also using the slug to identify which event
    path('<slug:slug>/register/', views.register_for_event, name='register'),
    
    # Bonus: URLs to generate PDF posters for the event
    path('<slug:slug>/poster/', views.generate_event_poster, name='poster'),
    path('<slug:slug>/itinerary/', views.generate_itinerary_pdf, name='itinerary'),
    path('<slug:slug>/export/', views.export_registrations_excel, name='export_excel'),
]