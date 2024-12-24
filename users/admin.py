from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    # Customize the admin interface for the user model
    list_display = ('email', 'username', 'is_staff', 'is_active', 'coins')  # Add coins to list_display
    search_fields = ('email', 'username')
    ordering = ('email',)

    # Specify the fieldsets to organize the admin form
    fieldsets = (
        (None, {'fields': ('username', 'email', 'password')}),
        ('Personal Info', {'fields': ('bio', 'profile_picture', 'coins')}),  # Add coins here
        ('Permissions', {'fields': ('is_staff', 'is_active', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )

    # Fields to display when creating a new user in the admin panel
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2', 'is_staff', 'is_active', 'coins')},
         # Add coins here
         ),
    )
