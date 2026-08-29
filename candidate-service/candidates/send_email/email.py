from django.conf import settings
from django.core.mail import send_mail


def send_email(
    recipient_email,
    subject,
    message,
):
    """
    Generic email sender.
    """
    return send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[recipient_email],
        fail_silently=False,
    )


def send_application_reviewed_email(
    candidate_email,
    candidate_name,
    job_title,
):
    """
    Notify candidate when their application is reviewed.
    """

    subject = f"Application Reviewed - {job_title}"

    message = f"""
Hello {candidate_name},

Your application for the position "{job_title}" has been reviewed.

Please log in to your dashboard to see the latest status.

Best regards,
Job Management System
"""

    return send_email(
        recipient_email=candidate_email,
        subject=subject,
        message=message,
    )


def send_application_accepted_email(
    candidate_email,
    candidate_name,
    job_title,
):
    """
    Notify candidate when their application is accepted.
    """

    subject = f"Application Accepted - {job_title}"

    message = f"""
Congratulations {candidate_name}!

Your application for the position "{job_title}" has been accepted.

Please log in to your dashboard for more information.

Best regards,
Job Management System
"""

    return send_email(
        recipient_email=candidate_email,
        subject=subject,
        message=message,
    )


def send_application_rejected_email(
    candidate_email,
    candidate_name,
    job_title,
):
    """
    Notify candidate when their application is rejected.
    """

    subject = f"Application Update - {job_title}"

    message = f"""
Hello {candidate_name},

Thank you for your interest in the position "{job_title}".

After reviewing your application, we regret to inform you that
your application was not selected at this time.

We appreciate your time and interest.

Best regards,
Job Management System
"""

    return send_email(
        recipient_email=candidate_email,
        subject=subject,
        message=message,
    )


def send_job_match_email(
    candidate_email,
    candidate_name,
    job_title,
    matched_skills,
):
    """
    Notify a candidate when a newly created job matches their skills.
    """

    skills = ", ".join(matched_skills)

    subject = f"New Job Match - {job_title}"

    message = f"""
Hello {candidate_name},

A new job has been posted that matches your skills.

Job: {job_title}

Matched skills:
{skills}

Please log in to your dashboard to view the job and apply.

Best regards,
Job Management System
"""

    return send_email(
        recipient_email=candidate_email,
        subject=subject,
        message=message,
    )