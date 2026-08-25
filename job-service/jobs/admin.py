from django.contrib import admin
from jobs.models import Job, Application


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'company', 'location', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('title', 'company', 'location', 'description')
    ordering = ('-created_at',)


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ('id', 'job', 'candidate_name', 'candidate_email', 'status', 'applied_at')
    list_filter = ('status', 'applied_at')
    search_fields = ('candidate_name', 'candidate_email', 'job__title', 'job__company')
    ordering = ('-applied_at',)

