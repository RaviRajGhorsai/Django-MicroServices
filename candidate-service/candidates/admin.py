from django.contrib import admin
from .models import Candidate, JobApplication


class JobApplicationInline(admin.TabularInline):
    model = JobApplication
    extra = 0
    readonly_fields = ('applied_at', 'updated_at')
    fields = ('job_id', 'job_title', 'job_company', 'status', 'applied_at')


@admin.register(Candidate)
class CandidateAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'email', 'phone', 'experience_years', 'location', 'created_at')
    list_filter = ('experience_years', 'created_at')
    search_fields = ('name', 'email', 'phone', 'location')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-created_at',)
    inlines = [JobApplicationInline]


@admin.register(JobApplication)
class JobApplicationAdmin(admin.ModelAdmin):
    list_display = ('id', 'candidate', 'job_id', 'job_title', 'job_company', 'status', 'applied_at')
    list_filter = ('status', 'applied_at', 'job_company')
    search_fields = ('job_title', 'job_company', 'candidate__name', 'candidate__email')
    readonly_fields = ('applied_at', 'updated_at')
    ordering = ('-applied_at',)

