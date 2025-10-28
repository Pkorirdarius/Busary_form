# backend_logic/tasks.py
# Celery tasks for handling async operations

from celery import shared_task
from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.utils import timezone
from .models import BursaryApplication, Document
import logging

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def send_application_confirmation_email(self, application_id):
    """
    Send confirmation email to applicant after submission.
    This runs asynchronously to avoid blocking the web request.
    """
    try:
        application = BursaryApplication.objects.select_related(
            'user_profile__user'
        ).get(id=application_id)
        
        user = application.user_profile.user
        
        # Render email template
        context = {
            'applicant_name': application.student_name,
            'application_number': application.application_number,
            'submitted_date': application.submitted_at,
            'institution': application.institution_name,
            'amount_requested': application.amount_requested,
        }
        
        html_content = render_to_string('emails/application_confirmation.html', context)
        text_content = render_to_string('emails/application_confirmation.txt', context)
        
        # Create email
        email = EmailMultiAlternatives(
            subject=f'Bursary Application Confirmation - {application.application_number}',
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[user.email],
        )
        email.attach_alternative(html_content, "text/html")
        
        # Send email
        email.send()
        
        logger.info(f"Confirmation email sent for application {application.application_number}")
        return f"Email sent successfully to {user.email}"
        
    except BursaryApplication.DoesNotExist:
        logger.error(f"Application {application_id} not found")
        return f"Application {application_id} not found"
        
    except Exception as exc:
        logger.error(f"Error sending email for application {application_id}: {exc}")
        # Retry with exponential backoff
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))


@shared_task(bind=True, max_retries=3)
def send_status_update_email(self, application_id, old_status, new_status):
    """
    Send email notification when application status changes.
    """
    try:
        application = BursaryApplication.objects.select_related(
            'user_profile__user'
        ).get(id=application_id)
        
        user = application.user_profile.user
        
        context = {
            'applicant_name': application.student_name,
            'application_number': application.application_number,
            'old_status': old_status,
            'new_status': new_status,
            'status_display': application.get_status_display(),
            'reviewer_comments': application.reviewer_comments,
        }
        
        html_content = render_to_string('emails/status_update.html', context)
        text_content = render_to_string('emails/status_update.txt', context)
        
        email = EmailMultiAlternatives(
            subject=f'Bursary Application Status Update - {application.application_number}',
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[user.email],
        )
        email.attach_alternative(html_content, "text/html")
        email.send()
        
        logger.info(f"Status update email sent for application {application.application_number}")
        return f"Status update email sent to {user.email}"
        
    except Exception as exc:
        logger.error(f"Error sending status update email: {exc}")
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))


@shared_task
def process_document_upload(document_id):
    """
    Process uploaded documents (virus scan, compression, etc.)
    This can be extended to include actual processing logic.
    """
    try:
        document = Document.objects.get(id=document_id)
        
        # Placeholder for document processing
        # You can add virus scanning, compression, or other processing here
        
        logger.info(f"Processed document {document.id} for application {document.application.application_number}")
        return f"Document {document_id} processed successfully"
        
    except Document.DoesNotExist:
        logger.error(f"Document {document_id} not found")
        return f"Document {document_id} not found"


@shared_task
def cleanup_old_pending_applications():
    """
    Periodic task to clean up old pending applications (e.g., older than 90 days)
    Run this task daily via Celery Beat.
    """
    from datetime import timedelta
    
    cutoff_date = timezone.now() - timedelta(days=90)
    
    old_applications = BursaryApplication.objects.filter(
        status='pending',
        created_at__lt=cutoff_date
    )
    
    count = old_applications.count()
    
    # You might want to archive instead of delete
    # old_applications.update(status='archived')
    
    logger.info(f"Found {count} old pending applications")
    return f"Processed {count} old applications"


@shared_task
def generate_daily_report():
    """
    Generate daily statistics report for administrators.
    Run this task daily at a specific time via Celery Beat.
    """
    from django.db.models import Count, Sum, Avg, Q
    
    today = timezone.now().date()
    
    stats = {
        'date': today,
        'total_applications': BursaryApplication.objects.filter(
            submitted_at__date=today
        ).count(),
        'pending': BursaryApplication.objects.filter(
            status='pending'
        ).count(),
        'approved': BursaryApplication.objects.filter(
            status='approved',
            reviewed_at__date=today
        ).count(),
        'rejected': BursaryApplication.objects.filter(
            status='rejected',
            reviewed_at__date=today
        ).count(),
    }
    
    # Send report to administrators
    admin_emails = ['admin@westpokot.go.ke']
    
    context = {'stats': stats}
    html_content = render_to_string('emails/daily_report.html', context)
    
    email = EmailMultiAlternatives(
        subject=f'Daily Bursary Report - {today}',
        body=f"Daily report for {today}",
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=admin_emails,
    )
    email.attach_alternative(html_content, "text/html")
    email.send()
    
    logger.info(f"Daily report sent for {today}")
    return f"Daily report generated and sent"


@shared_task(bind=True)
def bulk_update_application_status(self, application_ids, new_status, comments=''):
    """
    Bulk update application statuses.
    Useful for admin actions.
    """
    try:
        applications = BursaryApplication.objects.filter(id__in=application_ids)
        count = applications.count()
        
        applications.update(
            status=new_status,
            reviewed_at=timezone.now(),
            reviewer_comments=comments
        )
        
        # Send individual status update emails
        for app_id in application_ids:
            send_status_update_email.delay(app_id, 'pending', new_status)
        
        logger.info(f"Bulk updated {count} applications to {new_status}")
        return f"Updated {count} applications"
        
    except Exception as exc:
        logger.error(f"Error in bulk update: {exc}")
        raise self.retry(exc=exc, countdown=60)