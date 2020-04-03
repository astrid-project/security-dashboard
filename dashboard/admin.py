from django.contrib import admin

from .models import Service, SecurityPolicy, Customer, Log

# class SecurityPolicyInline(admin.TabularInline):
#     model = SecurityPolicy
#     extra = 3
#
# class ServiceAdmin(admin.ModelAdmin):
#     inlines = [SecurityPolicyInline]

class SecurityPolicyAdmin(admin.ModelAdmin):
    list_display = ('policy_id', 'policy_sla', 'policy_name',
                    'policy_description', 'last_modified')


admin.site.register(Service)
admin.site.register(SecurityPolicy, SecurityPolicyAdmin)
admin.site.register(Customer)
admin.site.register(Log)
