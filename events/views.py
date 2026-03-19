from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Event, AudienceCategory, Registration
from .forms import RegistrationForm
from django.http import JsonResponse, HttpResponse
from django.template.loader import render_to_string
from django.urls import reverse
from django.core.mail import send_mail
from django.conf import settings
from xhtml2pdf import pisa
from django.contrib.admin.views.decorators import staff_member_required
import qrcode
import base64
from io import BytesIO
from datetime import date
import os
from django.conf import settings
import openpyxl
from django.http import HttpResponse

def event_list(request):
    # Get today's date so we only show upcoming events
    today = timezone.now().date()
    
    # Fetch events from the database that happen today or in the future
    # .select_related() makes the database query faster when grabbing the category name
    upcoming_events = Event.objects.filter(date__gte=today).select_related('category')
    
    # Fetch all categories to build the filter buttons dynamically
    categories = AudienceCategory.objects.all()

    # Pass the data to the HTML template
    context = {
        'events': upcoming_events,
        'categories': categories,
    }
    return render(request, 'events/list.html', context)

def event_detail(request, slug):
    event = get_object_or_404(Event, slug=slug)
    
    # Check if the user is already registered (using email if logged in)
    is_registered = False
    initial_data = {}
    
    if request.user.is_authenticated:
        is_registered = Registration.objects.filter(event=event, user=request.user).exists()
        # Pre-fill the form to save the user time
        initial_data = {
            'full_name': f"{request.user.first_name} {request.user.last_name}".strip() or request.user.username,
            'email': request.user.email,
            'id_number': request.user.student_id,
        }
        
    form = RegistrationForm(initial=initial_data)
        
    context = {
        'event': event,
        'is_registered': is_registered,
        'form': form,
    }
    return render(request, 'events/detail.html', context)

def register_for_event(request, slug):
    event = get_object_or_404(Event, slug=slug)
    
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        
        if form.is_valid():
            email = form.cleaned_data['email']
            
            # 1. Prevent duplicate registrations
            if Registration.objects.filter(event=event, email=email).exists():
                messages.warning(request, "A registration with this email already exists for this event.")
                return redirect('events:detail', slug=slug)

            # 2. Logic for Capacity and Waitlist
            # Count only confirmed registrations
            confirmed_count = event.registrations.filter(status='confirmed').count()
            
            registration = form.save(commit=False)
            registration.event = event
            if request.user.is_authenticated:
                registration.user = request.user

            if confirmed_count >= event.capacity:
                registration.status = 'waitlisted'
                success_message = f"The event is full, but you've been added to the waitlist for {event.title}."
                subject = f"Waitlist Confirmation: {event.title}"
                body_intro = f"Hello {registration.full_name},\n\nYou have been added to the WAITLIST for '{event.title}' because the event is currently at maximum capacity."
            else:
                registration.status = 'confirmed'
                success_message = f"Success! You are now registered for {event.title}. A confirmation email has been sent."
                subject = f"Registration Confirmed: {event.title}"
                body_intro = f"Hello {registration.full_name},\n\nYour registration for '{event.title}' has been confirmed!"

            registration.save()
            
            # 3. SEND AUTOMATED EMAIL
            message = (
                f"{body_intro}\n\n"
                f"--- Event Details ---\n"
                f"Date: {event.date.strftime('%B %d, %Y')}\n"
                f"Time: {event.start_time.strftime('%I:%M %p')} to {event.end_time.strftime('%I:%M %p')}\n"
                f"Location: {event.location}\n\n"
                f"Status: {registration.get_status_display()}\n\n"
                f"If a spot becomes available for waitlisted guests, you will be notified via email.\n\n"
                f"Best regards,\n"
                f"Midlands State University Library"
            )
            
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [registration.email],
                fail_silently=False,
            )
            
            messages.success(request, success_message)
            return redirect('events:detail', slug=slug)
        else:
            messages.error(request, "Please correct the errors in the form below.")
            context = {'event': event, 'is_registered': False, 'form': form}
            return render(request, 'events/detail.html', context)
            
    return redirect('events:detail', slug=slug)

def calendar_view(request):
    # This view just renders the HTML page where the calendar will live
    return render(request, 'events/calendar.html')

def calendar_api(request):
    # This view grabs all events and formats them for FullCalendar.js
    events = Event.objects.all()
    events_data = []
    
    for event in events:
        # Combine date and time into ISO 8601 format (which FullCalendar requires)
        start_datetime = f"{event.date.isoformat()}T{event.start_time.strftime('%H:%M:%S')}"
        end_datetime = f"{event.date.isoformat()}T{event.end_time.strftime('%H:%M:%S')}"
        
        events_data.append({
            'title': event.title,
            'start': start_datetime,
            'end': end_datetime,
            # Generate the clickable link to the event details page
            'url': reverse('events:detail', kwargs={'slug': event.slug}),
            'backgroundColor': '#0d47a1', # MSU Blue
            'borderColor': '#0d47a1',
            'textColor': '#ffffff'
        })
        
    return JsonResponse(events_data, safe=False)

@staff_member_required(login_url='/accounts/login/')
def generate_event_poster(request, slug):
    primary_event = get_object_or_404(Event, slug=slug)
    
    upcoming_events = Event.objects.filter(
        date__gte=primary_event.date
    ).exclude(
        id=primary_event.id
    ).order_by('date', 'start_time')[:3]
    
    events = [primary_event] + list(upcoming_events)
    
    # --- NEW: GENERATE THE QR CODE ---
    # 1. Define where the QR code points (The main events list)
    target_url = request.build_absolute_uri(reverse('events:list'))
    
    # 2. Create the QR image (We are making it MSU Blue!)
    qr = qrcode.QRCode(version=1, box_size=10, border=1)
    qr.add_data(target_url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="#0d47a1", back_color="white")
    
    # 3. Convert the image to a Base64 string so the PDF can read it easily
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    qr_base64 = base64.b64encode(buffer.getvalue()).decode()
    qr_data_uri = f"data:image/png;base64,{qr_base64}"
    # ---------------------------------
    
    context = {
        'events': events, 
        'logo_url': request.build_absolute_uri('/static/images/msu_logo.jpg'), 
        'qr_code': qr_data_uri, # Pass the generated QR code to the template
    }
    
    html_string = render_to_string('events/multi_poster.html', context)
    filename = f"{primary_event.date.strftime('%B')}_Event_Series.pdf"
    
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    pisa_status = pisa.CreatePDF(html_string, dest=response)
    
    if pisa_status.err:
        return HttpResponse('We had some errors <pre>' + html_string + '</pre>')
    return response

def generate_itinerary_pdf(request, slug):
    # 1. Fetch the event
    event = get_object_or_404(Event, slug=slug)
    
    # 2. Fetch all agenda items linked to this event (ordered by time automatically)
    agenda_items = event.agenda_items.all()
    
    # 3. Build context
    context = {
        'event': event,
        'agenda_items': agenda_items,
        'logo_url': request.build_absolute_uri('/static/images/msu_logo.jpg'),
    }
    
    # 4. Render the HTML
    html_string = render_to_string('events/itinerary_poster.html', context)
    filename = f"{event.slug}_workshop_program.pdf"
    
    # 5. Generate PDF
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    pisa_status = pisa.CreatePDF(html_string, dest=response)
    if pisa_status.err:
        return HttpResponse('We had some errors <pre>' + html_string + '</pre>')
    return response

def generate_monthly_series_poster(request):
    # 1. Find the very next upcoming event
    first_upcoming = Event.objects.filter(
        date__gte=date.today()
    ).order_by('date', 'start_time').first()
    
    if not first_upcoming:
        return HttpResponse("No upcoming events found to generate a poster.")
        
    target_month = first_upcoming.date.month
    target_year = first_upcoming.date.year
    
    upcoming_events = Event.objects.filter(
        date__gte=date.today(),
        date__month=target_month,
        date__year=target_year
    ).order_by('date', 'start_time')[:4]
        
    # --- NEW: GRAB THE CUSTOM HEADING ---
    # We look for the text you typed. If you typed nothing, we use a fallback.
    custom_heading = request.GET.get('heading', '').strip()
    if not custom_heading:
        custom_heading = f"{first_upcoming.date.strftime('%B')} EVENT SERIES"
    # ------------------------------------

    target_url = request.build_absolute_uri(reverse('events:list'))
    qr = qrcode.QRCode(version=1, box_size=10, border=1)
    qr.add_data(target_url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="#0d47a1", back_color="white")
    
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    qr_base64 = base64.b64encode(buffer.getvalue()).decode()
    qr_data_uri = f"data:image/png;base64,{qr_base64}"
    
    logo_path = os.path.join(settings.BASE_DIR, 'static', 'images', 'msu_logo.jpg')
    try:
        with open(logo_path, "rb") as image_file:
            logo_base64 = base64.b64encode(image_file.read()).decode('utf-8')
            ext = logo_path.split('.')[-1].lower()
            mime_type = f"image/{ext}" if ext != 'jpg' else "image/jpeg"
            logo_data_uri = f"data:{mime_type};base64,{logo_base64}"
    except FileNotFoundError:
        return HttpResponse(f"Error: Could not find the logo at {logo_path}")
    
    # 4. Build context
    context = {
        'events': upcoming_events, 
        'logo_url': logo_data_uri,
        'qr_code': qr_data_uri,
        'custom_heading': custom_heading, # Pass the heading to the PDF!
    }
    
    html_string = render_to_string('events/multi_poster.html', context)
    
    filename = f"{first_upcoming.date.strftime('%B')}_Series_Poster.pdf"
    
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    pisa_status = pisa.CreatePDF(html_string, dest=response)
    if pisa_status.err:
        return HttpResponse('We had some errors <pre>' + html_string + '</pre>')
    return response

@staff_member_required
def export_registrations_excel(request, slug):
    event = get_object_or_404(Event, slug=slug)
    registrations = event.registrations.all().order_by('status', 'created_at')

    # Create workbook and sheet
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Registrations"

    # Header Row
    headers = ['Full Name', 'Email', 'ID Number', 'Status', 'Date Joined']
    ws.append(headers)

    # Data Rows
    for reg in registrations:
        ws.append([
            reg.full_name, 
            reg.email, 
            getattr(reg, 'id_number', 'N/A'), 
            reg.status, 
            reg.created_at.strftime('%Y-%m-%d %H:%M')
        ])

    # Prepare response
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    )
    response['Content-Disposition'] = f'attachment; filename={slug}_registrations.xlsx'
    wb.save(response)
    return response