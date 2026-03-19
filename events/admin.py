from django.contrib import admin
from .models import AudienceCategory, Event, Registration, AgendaItem
from django.utils.html import format_html
from xhtml2pdf import pisa
from django.template.loader import render_to_string
from django.http import HttpResponse

# 1. DEFINE THE MULTI-POSTER GENERATOR FUNCTION
@admin.action(description='Generate Multi-Event Poster (PDF)')
def generate_multi_poster(modeladmin, request, queryset):
    # Sort the selected events by date, and limit to 4 so it fits on one page perfectly
    events = queryset.order_by('date', 'start_time')[:4]
    
    # Render the HTML template
    html_string = render_to_string('events/multi_poster.html', {'events': events})
    
    # Create the PDF response
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="library_series_poster.pdf"'
    
    # Convert HTML to PDF
    pisa_status = pisa.CreatePDF(html_string, dest=response)
    if pisa_status.err:
        return HttpResponse('We had some errors <pre>' + html_string + '</pre>')
    return response

@admin.register(AudienceCategory)
class AudienceCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    # The slug will auto-fill as you type the name in the admin panel
    prepopulated_fields = {'slug': ('name',)}

# 1. CREATE THE INLINE FORM
class AgendaItemInline(admin.TabularInline):
    model = AgendaItem
    extra = 1 # Shows 1 empty row by default
    fields = ('start_time', 'end_time', 'activity', 'speaker')

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('title', 'date', 'start_time', 'location', 'category', 'capacity')
    list_filter = ('category', 'date')
    search_fields = ('title', 'location', 'description')
    prepopulated_fields = {'slug': ('title',)}
    # We can also add a read-only field to show the shareable link for the event in the admin detail view
    readonly_fields = ('shareable_link',)
    inlines = [AgendaItemInline]
    actions = [generate_multi_poster]

    def shareable_link(self, obj):
        if obj.id: # Check if the event has been saved to the database yet
            url = obj.get_absolute_url()
            return format_html('<a href="{}" target="_blank" style="background: #0d47a1; color: white; padding: 5px 10px; border-radius: 4px; text-decoration: none;">View Event & Copy Link</a>', url)
        return "Save the event first to generate a link."
    shareable_link.short_description = "Shareable Event Link"
    # Optional: Automatically set the 'created_by' field to the logged-in admin user
    def save_model(self, request, obj, form, change):
        if not getattr(obj, 'created_by_id', None):
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

@admin.register(Registration)
class RegistrationAdmin(admin.ModelAdmin):
    list_display = ('user', 'event', 'registered_at', 'attended')
    list_filter = ('event', 'attended')
    search_fields = ('user__username', 'user__student_id', 'event__title')



