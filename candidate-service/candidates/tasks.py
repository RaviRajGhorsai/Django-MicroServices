from config.celery import app
import logging

logger = logging.getLogger(__name__)

@app.task(bind=True, max_retries=3, default_retry_delay=60, queue='candidate-service')
def index_candidate_in_opensearch(self, candidate_id: int):
    try:
        from candidates.models import Candidate
        from candidates.search import index_candidate
        candidate = Candidate.objects.get(pk=candidate_id)
        index_candidate(candidate)
    except Exception as exc:
        raise self.retry(exc=exc)

@app.task(queue='candidate-service')
def send_job_match_notification(candidate_id: int, candidate_email: str,
                                job_title: str, matched_skills: list):
    logger.info(
        f"[EMAIL→CANDIDATE] Job match for candidate {candidate_id}: "
        f"'{job_title}' | matched skills: {matched_skills} → {candidate_email}"
    )

@app.task(queue='candidate-service')
def send_application_status_update(application_id: int, status: str):
    logger.info(
        f"[EMAIL→CANDIDATE] Application status updated for candidate {application_id}: {status}"
    )