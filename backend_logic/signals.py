from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from django.utils import timezone
from .models import BursaryApplication


@receiver(pre_save, sender=BursaryApplication)
def update_reviewed_timestamp(sender, instance, **kwargs):
    """
    Automatically update reviewed_at timestamp when status changes
    from 'pending' to any other status
    """
    if instance.pk:  # Only for existing records
        try:
            old_instance = BursaryApplication.objects.get(pk=instance.pk)
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
def log_application_status_change(sender, instance, created, **kwargs):
    """
    Log application status changes for audit trail
    You can extend this to send notifications, emails, etc.
    """
    if created:
        # New application created
        print(f"New application created: {instance.application_number}")
        # TODO: Send confirmation email to applicant
    else:
        # Application updated
        print(f"Application {instance.application_number} updated - Status: {instance.status}")
        # TODO: Send status update email to applicant


# Optional: Create an ApplicationStatusLog model for detailed tracking
from django.db import models
from django.contrib.auth.models import User


# class ApplicationStatusLog(models.Model):
#     """
#     Model to track all status changes for analytics and audit purposes
#     """
#     application = models.ForeignKey(
#         BursaryApplication,
#         on_delete=models.CASCADE,
#         related_name='status_logs'
#     )
#     old_status = models.CharField(max_length=20, blank=True)
#     new_status = models.CharField(max_length=20)
#     changed_by = models.ForeignKey(
#         User,
#         on_delete=models.SET_NULL,
#         null=True,
#         blank=True
#     )
#     comments = models.TextField(blank=True)
#     changed_at = models.DateTimeField(auto_now_add=True)

#     class Meta:
#         verbose_name = "Application Status Log"
#         verbose_name_plural = "Application Status Logs"
#         ordering = ['-changed_at']

#     def __str__(self):
#         return f"{self.application.application_number}: {self.old_status} → {self.new_status}"


@receiver(pre_save, sender=BursaryApplication)
def create_status_log(sender, instance, **kwargs):
    """
    Create a log entry whenever status changes
    """
    if instance.pk:
        try:
            old_instance = BursaryApplication.objects.get(pk=instance.pk)
            if old_instance.status != instance.status:
                # Create log entry after save
                # We'll use post_save for this to ensure the application is saved first
                instance._status_changed = True
                instance._old_status = old_instance.status
        except BursaryApplication.DoesNotExist:
            pass


@receiver(post_save, sender=BursaryApplication)
def save_status_log(sender, instance, created, **kwargs):
    """
    Save the status log entry after application is saved
    """
    if hasattr(instance, '_status_changed') and instance._status_changed:
        ApplicationStatusLog.objects.create(
            application=instance,
            old_status=instance._old_status,
            new_status=instance.status,
            comments=instance.reviewer_comments
        )
        # Clean up temporary attributes
        del instance._status_changed
        del instance._old_status