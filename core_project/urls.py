"""
URL configuration for core_project project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include

admin.site.site_header = 'MSU Library Events Admin'
admin.site.site_title = 'Library Events Portal'
admin.site.index_title = 'Welcome to the Events Management Portal'

urlpatterns = [
    path('admin/', admin.site.urls),
    # Include the URLs from the events app, which will handle all event-related pages
    path('analytics/', include('analytics.urls', namespace='analytics')),
    # The empty string '' means this is the main page for events, so it will be the homepage of the site
    path('', include('events.urls', namespace='events')),
    
]
