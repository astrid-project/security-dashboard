from django.contrib import admin

from .models import Service, SecurityPolicy

class SecurityPolicyInline(admin.TabularInline):
    model = SecurityPolicy
    extra = 3

class ServiceAdmin(admin.ModelAdmin):
    inlines = [SecurityPolicyInline]

admin.site.register(Service, ServiceAdmin)
