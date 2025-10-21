from django.db import models
from django.conf import settings
# Create your models here.


def upload_to(instance, filename):
    return f"documents/{instance.application.id}/{filename}"

class UserProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    phone = models.CharField(max_length=20)
    id_number = models.CharField(max_length=20, unique=True)
    county = models.CharField(max_length=50)
    ward = models.CharField(max_length=50)
    location = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.user.username} - {self.id_number}"


class BursaryApplication(models.Model):
    STATUS_CHOICES = [
        ("Pending", "Pending"),
        ("Approved", "Approved"),
        ("Rejected", "Rejected"),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    institution_name = models.CharField(max_length=100)
    tuition_fee = models.DecimalField(max_digits=10, decimal_places=2)
    amount_requested = models.DecimalField(max_digits=10, decimal_places=2)
    siblings_total = models.PositiveIntegerField(default=0)
    siblings_in_school = models.PositiveIntegerField(default=0)
    family_income = models.DecimalField(max_digits=10, decimal_places=2)
    reason_for_application = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="Pending")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.amount_requested > self.tuition_fee:
            raise ValidationError("Requested amount cannot exceed tuition fee.")
        if self.siblings_in_school > self.siblings_total:
            raise ValidationError("Siblings in school cannot exceed total siblings.")
        if self.family_income < 0:
            raise ValidationError("Family income cannot be negative.")

    def __str__(self):
        return f"{self.user.username} - {self.institution_name} ({self.status})"


class Document(models.Model):
    application = models.ForeignKey(BursaryApplication, on_delete=models.CASCADE, related_name="documents")
    file = models.FileField(upload_to=upload_to)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Document for {self.application}"
