from django.contrib import admin

from .models import (AgentTemplate, SecurityPolicyTemplate, Service,
                     SecurityPolicy, Customer, Log,
                     Agent, Algorithm, AlgorithmTemplate)
# class SecurityPolicyInline(admin.TabularInline):
#     model = SecurityPolicy
#     extra = 3
#
# class ServiceAdmin(admin.ModelAdmin):
#     inlines = [SecurityPolicyInline]

# class SecurityPolicyAdmin(admin.ModelAdmin):
#     list_display = ('policy_id', 'policy_sla', 'policy_name',
#                     'policy_description', 'last_modified')


admin.site.register(Service)
admin.site.register(SecurityPolicy)
admin.site.register(SecurityPolicyTemplate)
admin.site.register(Customer)
admin.site.register(Log)
admin.site.register(Agent)
admin.site.register(AgentTemplate)
admin.site.register(Algorithm)
admin.site.register(AlgorithmTemplate)