from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin
from .models import UserProfile

admin.site.unregister(User)  # Unregister the default first
admin.site.register(User, UserAdmin)  # Then re-register it
admin.site.register(UserProfile)