from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import UserProfile

class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'User Profile'
    fk_name = 'user'  # Specify which ForeignKey to use
    fields = ('approval_status', 'is_approved', 'approved_at', 'approved_by')
    readonly_fields = ('created_at', 'approved_at', 'approved_by')

class UserAdmin(BaseUserAdmin):
    inlines = (UserProfileInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'get_approval_status', 'date_joined')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'userprofile__approval_status')
    search_fields = ('username', 'first_name', 'last_name', 'email')
    
    def get_approval_status(self, obj):
        if hasattr(obj, 'userprofile'):
            return obj.userprofile.get_approval_status_display()
        return 'No Profile'
    get_approval_status.short_description = 'Approval Status'

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'approval_status', 'is_approved', 'created_at', 'approved_at', 'approved_by')
    list_filter = ('approval_status', 'is_approved', 'created_at')
    search_fields = ('user__username', 'user__email', 'user__first_name', 'user__last_name')
    readonly_fields = ('created_at', 'approved_at', 'approved_by')
    
    fieldsets = (
        ('User Information', {
            'fields': ('user',)
        }),
        ('Approval Status', {
            'fields': ('approval_status', 'is_approved')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'approved_at', 'approved_by'),
            'classes': ('collapse',)
        }),
    )

# Unregister the default User admin and register our custom one
admin.site.unregister(User)
admin.site.register(User, UserAdmin)