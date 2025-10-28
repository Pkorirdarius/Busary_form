# backend_logic/signals.py
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from django.utils import timezone
from .models import BursaryApplication, ApplicationStatusLog
import logging

logger = logging.getLogger(__name__)


@receiver(pre_save, sender=BursaryApplication)
def update_reviewed_timestamp(sender, instance, **kwargs):
    """
    Automatically update reviewed_at timestamp when status changes.
    Optimized to reduce database queries.
    """
    if instance.pk:
        try:
            # Use only() to fetch only needed fields
            old_instance = BursaryApplication.objects.only('status', 'reviewed_at').get(pk=instance.pk)
            
            # Check if status changed from pending
            if (old_instance.status == 'pending' and 
                instance.status != 'pending' and 
                not instance.reviewed_at):
                instance.reviewed_at = timezone.now()
            
            # Update reviewed_at if status changes to approved or rejected
            if (old_instance.status != instance.status and 
                instance.status in ['approved', 'rejected']):
                instance.reviewed_at = timezone.now()
                
        except BursaryApplication.DoesNotExist:
            pass


@receiver(post_save, sender=BursaryApplication)
def handle_application_save(sender, instance, created, **kwargs):
    """
    Handle post-save actions for applications.
    Triggers async tasks for email notifications.
    """
    try:
        # Import here to avoid circular imports
        from .tasks import send_application_confirmation_email, send_status_update_email
        
        if created:
            # New application created - send confirmation email asynchronously
            logger.info(f"New application created: {instance.application_number}")
            
            # Trigger async task to send confirmation email
            send_application_confirmation_email.delay(instance.id)
            
        else:
            # Application updated - check if status changed
            logger.info(f"Application {instance.application_number} updated - Status: {instance.status}")
            
    except ImportError:
        # If Celery/tasks not available, just log
        logger.warning("Celery tasks not available, skipping email notifications")
    except Exception as e:
        logger.error(f"Error in post_save signal: {e}")


@receiver(pre_save, sender=BursaryApplication)
def create_status_log_marker(sender, instance, **kwargs):
    """
    Mark instances that need status logging.
    Uses a temporary attribute to avoid extra queries.
    """
    if instance.pk:
        try:
            # Use only() for efficiency
            old_instance = BursaryApplication.objects.only('status').get(pk=instance.pk)
            
            if old_instance.status != instance.status:
                instance._status_changed = True
                instance._old_status = old_instance.status
                instance._new_status = instance.status
        except BursaryApplication.DoesNotExist:
            pass


@receiver(post_save, sender=BursaryApplication)
def save_status_log(sender, instance, created, **kwargs):
    """
    Save the status log entry and trigger status update email.
    Optimized to avoid unnecessary database queries.
    """
    if hasattr(instance, '_status_changed') and instance._status_changed:
        try:
            # Create log entry
            ApplicationStatusLog.objects.create(
                application=instance,
                old_status=instance._old_status,
                new_status=instance._new_status,
                comments=instance.reviewer_comments
            )
            
            # Trigger async email notification
            try:
                from .tasks import send_status_update_email
                send_status_update_email.delay(
                    instance.id,
                    instance._old_status,
                    instance._new_status
                )
            except ImportError:
                logger.warning("Celery not available, skipping status email")
            
        except Exception as e:
            logger.error(f"Error saving status log: {e}")
        finally:
            # Clean up temporary attributes
            if hasattr(instance, '_status_changed'):
                del instance._status_changed
            if hasattr(instance, '_old_status'):
                del instance._old_status
            if hasattr(instance, '_new_status'):
                del instance._new_status


@receiver(post_save, sender=BursaryApplication)
def cache_invalidation(sender, instance, **kwargs):
    """
    Invalidate relevant caches when an application is saved.
    This ensures cached data stays fresh.
    """
    from django.core.cache import cache
    
    try:
        # Invalidate list caches
        cache_keys = [
            'application_list_page_*',
            f'application_detail_{instance.pk}',
            f'user_applications_{instance.user_profile.user.pk}',
        ]
        
        for pattern in cache_keys:
            if '*' in pattern:
                # For Django-Redis, you can use delete_pattern
                # cache.delete_pattern(pattern)
                pass
            else:
                cache.delete(pattern)
                
    except Exception as e:
        logger.error(f"Cache invalidation error: {e}")