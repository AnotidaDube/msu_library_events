from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser

class CustomUserAdmin(UserAdmin):
    # Add our custom fields to the user editing screen in the admin panel
    fieldsets = UserAdmin.fieldsets + (
        ('MSU Library Details', {'fields': ('role', 'student_id')}),
    )
    
    # Add our custom fields to the user creation screen in the admin panel
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('MSU Library Details', {'fields': ('role', 'student_id')}),
    )
    
    # Display these columns in the user list view
    list_display = ['username', 'email', 'first_name', 'last_name', 'role', 'is_staff']

# Register our custom user model with our custom admin class
admin.site.register(CustomUser, CustomUserAdmin)