from django.contrib import admin

from .models import ScheduledPost, AuthenticationToken


class ScheduledPostAdmin(admin.ModelAdmin):
    list_display = ("status", "service", "scheduled_datetime", "is_posted")
    list_filter = ("service", "is_posted")

admin.site.register(ScheduledPost, ScheduledPostAdmin)
admin.site.register(AuthenticationToken)
