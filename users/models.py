from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    # Define the different types of users in our system
    ROLE_CHOICES = (
        ('student', 'Student'),
        ('faculty', 'Faculty Member'),
        ('library_staff', 'Library Staff'),
    )
    
    # Add custom fields to the default Django user
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='student')
    student_id = models.CharField(max_length=20, blank=True, null=True, unique=True)

    def __str__(self):
        # This controls how the user is displayed in the admin panel and elsewhere
        if self.student_id:
            return f"{self.first_name} {self.last_name} ({self.student_id})"
        return self.username