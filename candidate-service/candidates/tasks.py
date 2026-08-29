from config.celery import app
import logging

from candidates.send_email.email import (
    send_application_reviewed_email,
    send_application_accepted_email,
    send_application_rejected_email,
    send_job_match_email,
)

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
def send_job_match_notification(candidate_id: int, candidate_email: str, candidate_name: str,
                                job_title: str, matched_skills: list):

    logger.info(
        f"[EMAIL→CANDIDATE] Job match for candidate {candidate_id}: "
        f"'{job_title}' | matched skills: {matched_skills} → {candidate_email}"
    )

    try:
        send_job_match_email(
            candidate_email=candidate_email,
            candidate_name=candidate_name,
            job_title=job_title,
            matched_skills=matched_skills,
        )

        logger.info(
            "[EMAIL→CANDIDATE] Successfully sent job match email to %s",
            candidate_email,
        )

    except Exception:
        logger.exception(
            "[EMAIL→CANDIDATE] Failed to send job match email "
            "to %s for job '%s'",
            candidate_email,
            job_title,
        )

@app.task(queue="candidate-service")
def send_application_status_update(
    application_id: int,
    status: str,
):
    from candidates.models import JobApplication

    application = JobApplication.objects.select_related(
        "candidate"
    ).get(pk=application_id)

    candidate = application.candidate

    logger.info(
        "[EMAIL→CANDIDATE] Application %s status updated to '%s' for %s",
        application_id,
        status,
        candidate.email,
    )

    try:
        if status == "reviewed":
            send_application_reviewed_email(
                candidate_email=candidate.email,
                candidate_name=candidate.name,
                job_title=application.job_title,
            )

        elif status == "accepted":
            send_application_accepted_email(
                candidate_email=candidate.email,
                candidate_name=candidate.name,
                job_title=application.job_title,
            )

        elif status == "rejected":
            send_application_rejected_email(
                candidate_email=candidate.email,
                candidate_name=candidate.name,
                job_title=application.job_title,
            )

        else:
            logger.info(
                "[EMAIL→CANDIDATE] No email notification configured for status '%s'",
                status,
            )
            return

        logger.info(
            "[EMAIL→CANDIDATE] Successfully sent status '%s' email to %s",
            status,
            candidate.email,
        )

    except Exception:
        logger.exception(
            "[EMAIL→CANDIDATE] Failed to send status '%s' email for application %s",
            status,
            application_id,
        )