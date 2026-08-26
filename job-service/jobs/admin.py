from django.contrib import admin
from jobs.models import Job, Application, HRProfile

@admin.register(HRProfile)
class HRProfileAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'company', 'created_at')
    search_fields = ('user__email', 'user__username', 'company')
    ordering = ('-created_at',)


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'company', 'location', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('title', 'company', 'location', 'description')
    ordering = ('-created_at',)


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ('id', 'job', 'candidate_id', 'candidate_name', 'candidate_email', 'status', 'applied_at')
    list_filter = ('status', 'applied_at')
    search_fields = ('candidate_id', 'candidate_data__name', 'candidate_data__email', 'job__title', 'job__company')
    ordering = ('-applied_at',)

    @admin.display(description='Candidate Name')
    def candidate_name(self, obj):
        return obj.candidate_data.get('name', '-') if obj.candidate_data else '-'

    @admin.display(description='Candidate Email')
    def candidate_email(self, obj):
        return obj.candidate_data.get('email', '-') if obj.candidate_data else '-'


