from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth import get_user_model
from .models import ServiceRequest, UserProfile, ResolutionStep

User = get_user_model()

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'department')
    search_fields = ('user__username', 'user__email', 'department')
    list_filter = ('department',)

class ResolutionStepInline(admin.TabularInline):
    model = ResolutionStep
    extra = 1
    fields = ['step_number', 'description', 'created_by', 'created_at']
    readonly_fields = ['created_by', 'created_at']
    
    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

@admin.register(ServiceRequest)
class ServiceRequestAdmin(admin.ModelAdmin):
    list_display = ['id', 'requester_name', 'department', 'category', 'status', 'created_at', 'resolved_at']
    list_filter = ['status', 'category', 'department', 'created_at']
    search_fields = ['requester_name', 'department', 'description']
    inlines = [ResolutionStepInline]
    readonly_fields = ['created_at', 'updated_at', 'resolved_at']

@admin.register(ResolutionStep)
class ResolutionStepAdmin(admin.ModelAdmin):
    list_display = ['service_request', 'step_number', 'description', 'created_by', 'created_at']
    list_filter = ['created_at', 'created_by']
    search_fields = ['description', 'service_request__requester_name']
