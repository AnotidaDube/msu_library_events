from django.db import models
from django.conf import settings
from django.utils.text import slugify
from django.urls import reverse

class AudienceCategory(models.Model):
    name = models.CharField(max_length=50)
    slug = models.SlugField(unique=True, blank=True)

    def save(self, *args, **kwargs):
        # Automatically generate a URL-friendly slug from the name
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

class Event(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, blank=True)
    description = models.TextField()
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    
    # We use a standard CharField for location so it is a simple text input, not a dropdown.
    location = models.CharField(max_length=200, help_text="Venue name or online meeting link")
    
    poster = models.ImageField(upload_to='event_posters/', blank=True, null=True)
    capacity = models.PositiveIntegerField(
        null=True, 
        blank=True, 
        help_text="Maximum attendees allowed. Leave blank for unlimited."
    )
    category = models.ForeignKey(AudienceCategory, on_delete=models.SET_NULL, null=True, related_name='events')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='created_events')
    created_at = models.DateTimeField(auto_now_add=True)
    requires_registration = models.BooleanField(
        default=True,
        help_text="Uncheck this if the event is open to everyone (no RSVP needed)."
    )
    

    class Meta:
        ordering = ['date', 'start_time']
        indexes = [
            models.Index(fields=['date']),
        ]

    def save(self, *args, **kwargs):
        # Automatically generate a URL-friendly slug from the title
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

    @property
    def is_full(self):
        # If capacity is None, the event is unlimited, so it can never be full
        if self.capacity is None:
            return False
        # Otherwise, check if current registrations meet or exceed the limit
        return self.registrations.count() >= self.capacity

    def get_absolute_url(self):
        # This dynamically generates the URL path for this specific event
        return reverse('events:detail', kwargs={'slug': self.slug})

class Registration(models.Model):
    USER_TYPES = (
        ('student', 'Student'),
        ('staff', 'Staff / Faculty'),
        ('public', 'General Public'),
    )

    STATUS_CHOICES = [
        ('confirmed', 'Confirmed'),
        ('waitlisted', 'Waitlisted'),
    ]
    
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='registrations')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='registrations')
    
    full_name = models.CharField(max_length=150)
    email = models.EmailField()
    phone_number = models.CharField(max_length=20)
    user_type = models.CharField(max_length=20, choices=USER_TYPES, default='student')
    id_number = models.CharField(max_length=50, blank=True, null=True, help_text="Reg Number for Students, EC Number for Staff")
    department = models.CharField(max_length=100, blank=True, null=True, help_text="e.g., Computer Systems Engineering")
    
    special_requirements = models.TextField(blank=True, null=True, help_text="Any dietary needs or accessibility requirements?")
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='confirmed')
    registered_at = models.DateTimeField(auto_now_add=True)
    attended = models.BooleanField(default=False)

    class Meta:
        ordering = ['registered_at']

    def __str__(self):
        return f"{self.full_name} - {self.event.title} ({self.status})"

class AgendaItem(models.Model):
    # This links the agenda row directly to a specific event
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='agenda_items')
    
    start_time = models.TimeField()
    end_time = models.TimeField(null=True, blank=True) # Optional, in case an activity is just a specific time
    activity = models.CharField(max_length=255)
    speaker = models.CharField(max_length=255, blank=True, null=True) # Optional, e.g., "Lunch" doesn't need a speaker

    class Meta:
        # Automatically sort the itinerary by time
        ordering = ['start_time']

    def __str__(self):
        return f"{self.start_time.strftime('%H:%M')} - {self.activity}"