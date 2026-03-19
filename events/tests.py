from django.test import TestCase, Client
from django.urls import reverse
from datetime import date, time
from .models import Event, AudienceCategory, AgendaItem, Registration
from django.contrib.auth import get_user_model
User = get_user_model() # This automatically finds your 'CustomUser'
from .forms import RegistrationForm
from django.utils import timezone
import datetime
from .models import Event # Ensure this matches your models import
class MSUEventSystemTest(TestCase):

    
    def setUp(self):
        """Set up a complete environment for every test"""
        self.client = Client()
        
        # 1. CREATE A TEST USER (Required for created_by field)
        self.test_user = User.objects.create_user(username='admin', password='password123')
        
        # 2. Setup Category
        self.category = AudienceCategory.objects.create(
            name="Library Staff", 
            slug="library-staff"
        )
        
        # 3. Setup Event
        self.event = Event.objects.create(
            title="JOVE Workshop",
            slug="jove-workshop",
            date=date(2026, 3, 18),
            start_time=time(10, 0),
            end_time=time(15, 0),
            location="Senate Room",
            category=self.category,
            capacity=2,
            description="A training workshop for JOVE videos.",
            created_by=self.test_user  # ASSIGN THE USER HERE
        )
        
        # 4. Setup Agenda Item
        self.agenda = AgendaItem.objects.create(
            event=self.event,
            start_time=time(10, 5),
            activity="Welcome Remarks",
            speaker="Prof Maphosa"
        )

    # --- MODEL TESTS ---
    def test_event_str_method(self):
        self.assertEqual(str(self.event), "JOVE Workshop")

    def test_agenda_linking(self):
        """Check if agenda items are correctly linked to events"""
        self.assertEqual(self.event.agenda_items.count(), 1)
        self.assertEqual(self.event.agenda_items.first().activity, "Welcome Remarks")

    # --- VIEW & PAGE TESTS ---
    def test_event_list_page_status(self):
        response = self.client.get(reverse('events:list'))
        self.assertEqual(response.status_code, 200)

    def test_event_detail_page_status(self):
        response = self.client.get(reverse('events:detail', kwargs={'slug': self.event.slug}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "JOVE Workshop")

    # --- PDF GENERATION TESTS ---
    def test_itinerary_pdf_generation(self):
        """Test if the itinerary download returns a PDF"""
        url = reverse('events:itinerary', kwargs={'slug': self.event.slug})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')

    def test_series_poster_pdf_generation(self):
        """Test if the custom heading series poster returns a PDF"""

        
        # 1. Create a fake event 5 days in the future
        future_date = timezone.now().date() + datetime.timedelta(days=5)
        
        # Using dummy data based on your poster's layout requirements
       # 1. Create a fake event 5 days in the future
        future_date = timezone.now().date() + datetime.timedelta(days=5)
        
        # Only use fields that actually exist in your Event model!
        Event.objects.create(
            title="Python CI/CD Workshop",
            date=future_date,
            location="MSU Main Library",
            description="Testing the PDF generator"
        )
        # 2. Simulate typing a custom heading in the text box
        url = reverse('events:series_poster')
        response = self.client.get(url, {'heading': 'Custom Test Title'})
        
        # 3. Check the results
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf', msg=response.content)

    # --- FORM & REGISTRATION TESTS ---
    def test_successful_registration(self):
        """Test that a student can register via POST request"""
        url = reverse('events:register', kwargs={'slug': self.event.slug})
        data = {
            'full_name': 'Anotida Dube',
            'email': 'anotida@student.msu.ac.zw',
            'phone_number': '0771234567',
            'user_type': 'student',
            'id_number': 'R2310490M',
            'department': 'Engineering'
        }
        response = self.client.post(url, data)
        # Check if it redirects back to the detail page (status 302)
        self.assertEqual(response.status_code, 302)
        # Check if a Registration object was actually created
        self.assertEqual(Registration.objects.count(), 1)

    def test_event_capacity_limit(self):
        """Test that registration fails when the event is full"""
        # Fill up the 2 spots
        Registration.objects.create(event=self.event, full_name="User 1", email="u1@test.com")
        Registration.objects.create(event=self.event, full_name="User 2", email="u2@test.com")
        
        # Try to register a 3rd person
        url = reverse('events:register', kwargs={'slug': self.event.slug})
        data = {'full_name': 'User 3', 'email': 'u3@test.com'}
        response = self.client.post(url, data)
        
        # It should NOT create a new registration
        self.assertEqual(Registration.objects.count(), 2)

    

    def test_registration_form_invalid_email(self):
        """Test that the form rejects a bad email address"""
        form_data = {'full_name': 'Test', 'email': 'not-an-email', 'phone_number': '123'}
        form = RegistrationForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)