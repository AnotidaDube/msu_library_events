from django import forms
from .models import Registration

class RegistrationForm(forms.ModelForm):

    # This field is invisible to humans but visible to the HTML scrapers used by bots.
    website = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'style': 'display:none;', # Hides it visually from humans
            'tabindex': '-1',         # Prevents users from tabbing into it by accident
            'autocomplete': 'off'
        })
    )
    class Meta:
        model = Registration
        fields = ['full_name', 'email', 'phone_number', 'user_type', 'id_number', 'department', 'special_requirements']
        
        # We inject Tailwind CSS classes directly into the form inputs here
        widgets = {
            'full_name': forms.TextInput(attrs={'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-600', 'placeholder': 'e.g. Anotida Dube'}),
            'email': forms.EmailInput(attrs={'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-600', 'placeholder': 'student@msu.ac.zw'}),
            'phone_number': forms.TextInput(attrs={'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-600', 'placeholder': '+263 77 000 0000'}),
            'user_type': forms.Select(attrs={'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-600'}),
            'id_number': forms.TextInput(attrs={'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-600', 'placeholder': 'R2310490M or EC Number'}),
            'department': forms.TextInput(attrs={'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-600', 'placeholder': 'Computer Systems Engineering'}),
            'special_requirements': forms.Textarea(attrs={'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-600', 'rows': 2, 'placeholder': 'Dietary restrictions, wheelchair access, etc.'}),
        }

def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get('email')
        user_type = cleaned_data.get('user_type')
        id_number = cleaned_data.get('id_number')

        if email and user_type:
            email = email.lower()
            
            # --- Enforce Student Rules ---
            if user_type == 'student':
                if not id_number:
                     self.add_error('id_number', "Students must provide a Registration Number.")
                else:
                    id_number_upper = id_number.upper()
                    
                    # 1. Check if ID starts with R
                    if not id_number_upper.startswith('R'):
                        self.add_error('id_number', "Student Registration Numbers must start with the letter 'R'.")
                        
                    # 2. Check Email Domain
                    if not email.endswith('@students.msu.ac.zw'):
                        self.add_error('email', "Students must use their official @students.msu.ac.zw email address.")
                    else:
                        # 3. Cross-reference ID with Email Prefix
                        # This extracts the part before the '@' symbol and makes it uppercase
                        email_prefix = email.split('@')[0].upper()
                        
                        # Compare the extracted prefix with the provided ID number
                        if id_number_upper != email_prefix:
                            self.add_error('id_number', f"Your Registration Number must match the one in your email address ({email_prefix}).")
            
            # --- Enforce Staff Rules ---
            elif user_type == 'staff':
                if not email.endswith('@msu.ac.zw'):
                    self.add_error('email', "Staff must use their official @msu.ac.zw email address.")
                if not id_number:
                     self.add_error('id_number', "Staff must provide an EC Number.")
                
        return cleaned_data