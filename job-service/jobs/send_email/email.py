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


def send_application_submitted_email(
    recruiter_email,
    candidate_name,
    job_title,
):
    """
    Notify recruiter when a candidate applies for their job.
    """

    subject = f"New Application - {job_title}"

    message = f"""
Hello,

You have received a new application for the position:

Job: {job_title}
Candidate: {candidate_name}

Please log in to your dashboard to review the application.

Best regards,
Job Management System
"""

    return send_email(
        recipient_email=recruiter_email,
        subject=subject,
        message=message,
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
