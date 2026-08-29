from config.celery import app
import logging
from django.core.mail import BadHeaderError

from jobs.send_email.email import send_application_submitted_email

logger = logging.getLogger(__name__)

@app.task(bind=True, max_retries=3, default_retry_delay=60, queue='job-service')
def index_job_in_opensearch(self, job_id: int):
    print("OpenSearch indexing Job ID is" , job_id)
    try:
        from jobs.models import Job
        from jobs.search import index_job
        job = Job.objects.get(pk=job_id)
        index_job(job)
    except Exception as exc:
        raise self.retry(exc=exc)

@app.task(bind=True, max_retries=3, default_retry_delay=60, queue='job-service')
def index_application_in_opensearch(self, application_id: int):
    try:
        from jobs.models import Application
        from jobs.search import index_application
        app = Application.objects.select_related('job').get(pk=application_id)
        index_application(app)
    except Exception as exc:
        raise self.retry(exc=exc)

@app.task(queue='job-service')
def send_application_notification(job_id: int, candidate_name: str, candidate_email: str):
    from jobs.models import Job
    job = Job.objects.get(pk=job_id)
    logger.info(f"[EMAIL→HR] New application for '{job.title}' from {candidate_name} <{candidate_email}>")
    

    try:
        send_application_submitted_email(
            recruiter_email=job.posted_by.email,
            candidate_name=candidate_name,
            job_title=job.title,
        )
    except BadHeaderError:
    # Invalid email header
        print("Invalid email header while sending notification.")
    except Exception as exc:
    # Email failed, but don't fail the application request
        print(f"Failed to send application notification: {exc}")

@app.task(queue='job-service')
def close_expired_jobs():
    from django.utils import timezone
    from datetime import timedelta
    from jobs.models import Job
    from jobs.search import delete_job
    cutoff = timezone.now() - timedelta(days=30)
    for job in Job.objects.filter(status='active', created_at__lt=cutoff):
        job.status = 'closed'
        job.save()
        delete_job(job.id)
        logger.info(f"Auto-closed expired job {job.id}: {job.title}")
