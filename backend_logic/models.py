from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator, RegexValidator
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models import Index,UniqueConstraint


class UserProfile(models.Model):
    """Extended user profile for bursary applicants"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    phone_number = models.CharField(
        max_length=15,
        validators=[RegexValidator(r'^\+?1?\d{9,15}$', 'Enter a valid phone number')]
    )
    id_number = models.CharField(max_length=20, unique=True, db_index=True)  # Added index
    date_of_birth = models.DateField()
    county = models.CharField(max_length=100, db_index=True)  # Added index for filtering
    sub_county = models.CharField(max_length=100, db_index=True)  # Added index
    ward = models.CharField(max_length=100)
    village = models.CharField(max_length=100)
    location = models.CharField(max_length=100, default='', blank=True)
    sub_location = models.CharField(max_length=100, default='', blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.id_number}"

    class Meta:
        verbose_name = "User Profile"
        verbose_name_plural = "User Profiles"
        indexes = [
            Index(fields=['county', 'sub_county'], name='idx_location'),
            Index(fields=['id_number'], name='idx_id_number'),
        ]


class BursaryApplication(models.Model):
    """Main bursary application model with optimized indexing"""
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('under_review', 'Under Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    EDUCATION_LEVEL_CHOICES = [
        ('primary', 'Primary School'),
        ('secondary', 'Secondary School'),
        ('college', 'College'),
        ('university', 'University'),
    ]

    FAMILY_STATUS_CHOICES = [
        ('both_parents', 'Both Parents Alive'),
        ('single_parent', 'Single Parent'),
        ('orphan', 'Orphan'),
        ('guardian', 'Under Guardian'),
    ]

    # Applicant Information
    user_profile = models.ForeignKey(
        UserProfile, 
        on_delete=models.CASCADE, 
        related_name='applications',
        db_index=True  # Added index for joins
    )
    application_number = models.CharField(max_length=20, unique=True, editable=False, db_index=True)
    
    # Student Information
    student_name = models.CharField(max_length=200, db_index=True)  # Added index for search
    institution_name = models.CharField(max_length=200, db_index=True)  # Added index
    admission_number = models.CharField(max_length=50)
    education_level = models.CharField(max_length=20, choices=EDUCATION_LEVEL_CHOICES, db_index=True)
    course_program = models.CharField(max_length=200)
    year_of_study = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(8)]
    )
    inst_county = models.CharField(max_length=100, default='', blank=True)
    inst_contact = models.CharField(max_length=15, default='', blank=True)
    term1_score = models.CharField(max_length=50, default='', blank=True)
    term2_score = models.CharField(max_length=50, default='', blank=True)
    term3_score = models.CharField(max_length=50, default='', blank=True)

    # Financial Information
    annual_family_income = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    tuition_fee = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    amount_requested = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    
    # Family Information
    family_status = models.CharField(max_length=20, choices=FAMILY_STATUS_CHOICES, db_index=True)
    number_of_siblings = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(20)]
    )
    siblings_in_school = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(20)]
    )
    
    # Parent/Guardian Information
    parent_guardian_name = models.CharField(max_length=200)
    parent_guardian_phone = models.CharField(
        max_length=15,
        validators=[RegexValidator(r'^\+?1?\d{9,15}$', 'Enter a valid phone number')]
    )
    parent_guardian_occupation = models.CharField(max_length=100)
    father_name = models.CharField(max_length=200, default='', blank=True)
    mother_name = models.CharField(max_length=200, default='', blank=True)
    guardian_relation = models.CharField(max_length=100, default='', blank=True)
    father_occupation = models.CharField(max_length=100, default='', blank=True)
    mother_occupation = models.CharField(max_length=100, default='', blank=True)
    parent_id_number = models.CharField(max_length=20, default='', blank=True)
    is_single_parent = models.BooleanField(default=False, db_index=True)
    fees_provider = models.CharField(max_length=100, default='', blank=True)
    other_fees_provider = models.CharField(max_length=100, default='', blank=True)

    # Additional Information
    reason_for_application = models.TextField(max_length=1000)
    previous_bursary_recipient = models.BooleanField(default=False, db_index=True)
    cdf_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    ministry_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    county_gov_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    other_bursary_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    has_disability = models.BooleanField(default=False, db_index=True)
    disability_nature = models.CharField(max_length=255, default='', blank=True)
    disability_reg_no = models.CharField(max_length=50, default='', blank=True)
    is_orphan = models.BooleanField(default=False, db_index=True)

    # Declaration/Verification fields
    student_signature_name = models.CharField(max_length=200, default='')
    student_declaration_date = models.DateField(default=timezone.now)
    parent_signature_name = models.CharField(max_length=200, default='')
    parent_declaration_date = models.DateField(default=timezone.now)
    chief_full_name = models.CharField(max_length=200, default='', blank=True)
    chief_sub_location = models.CharField(max_length=100, default='', blank=True)
    chief_county = models.CharField(max_length=100, default='', blank=True)
    chief_sub_county = models.CharField(max_length=100, default='', blank=True)
    chief_location = models.CharField(max_length=100, default='', blank=True)
    chief_comments = models.TextField(max_length=500, default='', blank=True)
    chief_signature_name = models.CharField(max_length=200, default='', blank=True)
    chief_date = models.DateField(null=True, blank=True)

    # Application Status and Tracking
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='pending',
        db_index=True,
        help_text="Current status of the bursary application"
    )
    submitted_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        help_text="Timestamp when application was first submitted"
    )
    reviewed_at = models.DateTimeField(
        null=True, 
        blank=True,
        help_text="Timestamp when application was reviewed"
    )
    reviewer_comments = models.TextField(
        blank=True,
        help_text="Comments from the reviewer about the application"
    )
    
    # Metadata - Audit Trail
    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        help_text="Timestamp when record was created"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="Timestamp when record was last updated"
    )

    def __str__(self):
        return f"{self.application_number} - {self.student_name} ({self.get_status_display()})"

    def save(self, *args, **kwargs):
        if not self.application_number:
            import uuid
            self.application_number = f"BUR{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)

    @property
    def is_editable(self):
        """Check if application can be edited"""
        return self.status == 'pending'

    @property
    def days_since_submission(self):
        """Calculate days since application was submitted"""
        if self.submitted_at:
            delta = timezone.now() - self.submitted_at
            return delta.days
        return 0

    @property
    def approval_percentage(self):
        """Calculate what percentage of tuition fee is being requested"""
        if self.tuition_fee and self.tuition_fee > 0:
            return (self.amount_requested / self.tuition_fee) * 100
        return 0

    def get_status_color(self):
        """Return color code for status display"""
        status_colors = {
            'pending': '#FFA500',
            'under_review': '#2196F3',
            'approved': '#4CAF50',
            'rejected': '#F44336',
        }
        return status_colors.get(self.status, '#999999')
    # Verification and Flag fields (add after the status field)
    is_verified = models.BooleanField(
        default=False, 
        db_index=True,
        help_text="Has this application been verified by admin?"
    )
    verified_by = models.CharField(
        max_length=150, 
        blank=True,
        help_text="Username of admin who verified this application"
    )
    verified_at = models.DateTimeField(
        null=True, 
        blank=True,
        help_text="Timestamp when application was verified"
    )
    is_flagged = models.BooleanField(
        default=False, 
        db_index=True,
        help_text="Has this application been flagged for review?"
    )
    flag_reason = models.TextField(
        blank=True,
        help_text="Reason why this application was flagged"
    )

    class Meta:
        verbose_name = "Bursary Application"
        verbose_name_plural = "Bursary Applications"
        ordering = ['-submitted_at']
        indexes = [
            Index(fields=['-submitted_at'], name='idx_submitted_at'),
            Index(fields=['status', '-submitted_at'], name='idx_status_submitted'),
            Index(fields=['education_level', 'status'], name='idx_edu_status'),
            Index(fields=['user_profile', '-created_at'], name='idx_profile_created'),
            Index(fields=['is_orphan', 'status'], name='idx_orphan_status'),
            Index(fields=['has_disability', 'status'], name='idx_disability_status'),
        ]
        permissions = [
            ("review_application", "Can review bursary applications"),
            ("approve_application", "Can approve bursary applications"),
            ("reject_application", "Can reject bursary applications"),
            ("view_analytics", "Can view application analytics"),
        ]
        # Enforce that only one application can exist per user_profile
        constraints = [
            UniqueConstraint(fields=['user_profile'], name='unique_application_per_user')
        ]


class ApplicationStatusLog(models.Model):
    """Audit log for application status changes"""
    application = models.ForeignKey(
        BursaryApplication,
        on_delete=models.CASCADE,
        related_name='status_logs'
    )
    old_status = models.CharField(max_length=50)
    new_status = models.CharField(max_length=50)
    comments = models.TextField(blank=True)
    changed_at = models.DateTimeField(auto_now_add=True, db_index=True)

    def __str__(self):
        return f"Status change for {self.application.application_number}: {self.old_status} -> {self.new_status}"

    class Meta:
        verbose_name = "Application Status Log"
        verbose_name_plural = "Application Status Logs"
        ordering = ['-changed_at']
        indexes = [
            Index(fields=['application', '-changed_at'], name='idx_app_log'),
        ]


class Document(models.Model):
    """Model for storing application documents"""
    
    DOCUMENT_TYPE_CHOICES = [
        ('id_copy', 'ID Copy'),
        ('admission_letter', 'Admission Letter'),
        ('fee_structure', 'Fee Structure'),
        ('income_proof', 'Proof of Income'),
        ('parent_id', 'Parent/Guardian ID'),
        ('birth_certificate', 'Birth Certificate'),
        ('death_certificate', 'Death Certificate (if applicable)'),
        ('other', 'Other Document'),
    ]

    application = models.ForeignKey(
        BursaryApplication,
        on_delete=models.CASCADE,
        related_name='documents',
        db_index=True
    )
    document_type = models.CharField(max_length=30, choices=DOCUMENT_TYPE_CHOICES, db_index=True)
    file = models.FileField(upload_to='bursary_documents/%Y/%m/')
    description = models.CharField(max_length=200, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True, db_index=True)

    def __str__(self):
        return f"{self.get_document_type_display()} - {self.application.application_number}"
    # --- ADD THESE MISSING FIELDS ---
    is_flagged = models.BooleanField(
        default=False, 
        verbose_name="Flagged for Review"
    )
    is_verified = models.BooleanField(
        default=False, 
        verbose_name="Verified"
    )

    # Choices for the 'status' field
    STATUS_CHOICES = [
        ('pending', 'Pending Review'),
        ('verified', 'Verified (Pass)'),
        ('rejected', 'Rejected (Fail)'),
    ]

    status = models.CharField(
        max_length=50, 
        choices=STATUS_CHOICES, 
        default='pending',
        verbose_name="Verification Status"
    )
    # -------------------------------

    application = models.ForeignKey(
        BursaryApplication,
        on_delete=models.CASCADE,
        related_name='documents',
        db_index=True
    )
    class Meta:
        verbose_name = "Document"
        verbose_name_plural = "Documents"
        ordering = ['-uploaded_at']
        indexes = [
            Index(fields=['application', 'document_type'], name='idx_app_doc_type'),
            Index(fields=['is_verified', 'is_flagged', 'status'], name='idx_verification'),
        ]