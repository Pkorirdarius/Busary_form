from django.contrib import admin
from django.utils.html import format_html
from .models import UserProfile, BursaryApplication, Document


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """Admin interface for UserProfile"""
    list_display = ['user', 'id_number', 'phone_number', 'county', 'sub_county', 'location', 'created_at'] # ADDED sub_county, location
    list_filter = ['county', 'sub_county', 'created_at'] # ADDED sub_county
    search_fields = ['user__first_name', 'user__last_name', 'id_number', 'phone_number']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('User Information', {
            'fields': ('user',)
        }),
        ('Personal Details', {
            'fields': ('id_number', 'phone_number', 'date_of_birth')
        }),
        ('Location', {
            'fields': ('county', 'sub_county', 'ward', 'location', 'sub_location', 'village') # ADDED location, sub_location
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


class DocumentInline(admin.TabularInline):
# ... (DocumentInline remains the same)
    """Inline admin for documents"""
    model = Document
    extra = 1
    readonly_fields = ['uploaded_at']


@admin.register(BursaryApplication)
class BursaryApplicationAdmin(admin.ModelAdmin):
    """Admin interface for BursaryApplication"""
    list_display = [
        'application_number', 'student_name', 'education_level',
        'amount_requested', 'status_badge', 'submitted_at'
    ]
    list_filter = [
        'status', 'education_level', 'family_status',
        'previous_bursary_recipient', 'submitted_at', 'is_orphan', # ADDED is_orphan
        'has_disability', # ADDED has_disability
    ]
    search_fields = [
        'application_number', 'student_name', 'institution_name',
        'user_profile__user__email', 'admission_number', 'parent_guardian_name'
    ]
    readonly_fields = [
        'application_number', 'submitted_at', 'created_at', 'updated_at'
    ]
    inlines = [DocumentInline]
    date_hierarchy = 'submitted_at'
    
    actions = ['approve_applications', 'reject_applications', 'mark_under_review']
    
    fieldsets = (
        ('Application Info', {
            'fields': ('application_number', 'user_profile', 'status')
        }),
        ('Student Information', {
            'fields': (
                'student_name', 'institution_name', 'admission_number',
                'education_level', 'course_program', 'year_of_study',
                'inst_county', 'inst_contact', # ADDED inst fields
            )
        }),
        ('School Performance', { # NEW FIELDSET
            'fields': ('term1_score', 'term2_score', 'term3_score')
        }),
        ('Disability Status', { # NEW FIELDSET
            'fields': ('has_disability', 'disability_nature', 'disability_reg_no', 'is_orphan')
        }),
        ('Financial Information', {
            'fields': (
                'annual_family_income', 'tuition_fee', 'amount_requested'
            )
        }),
        ('Family Information', {
            'fields': (
                'family_status', 'number_of_siblings', 'siblings_in_school',
                'father_name', 'mother_name', 'father_occupation', 'mother_occupation',
                'is_single_parent', # ADDED is_single_parent
            )
        }),
        ('Parent/Guardian Information', {
            'fields': (
                'parent_guardian_name', 'guardian_relation', 'parent_guardian_phone',
                'parent_guardian_occupation', 'parent_id_number'
            )
        }),
        ('Financial Support & Bursary History', { # NEW FIELDSET
            'fields': (
                'fees_provider', 'other_fees_provider', 'previous_bursary_recipient',
                'cdf_amount', 'ministry_amount', 'county_gov_amount', 'other_bursary_amount'
            )
        }),
        ('Additional Information', {
            'fields': (
                'reason_for_application',
            )
        }),
        ('Declaration & Chief Verification', { # NEW FIELDSET
            'fields': (
                ('student_signature_name', 'student_declaration_date'),
                ('parent_signature_name', 'parent_declaration_date'),
                'chief_full_name', 'chief_sub_location', 'chief_county',
                'chief_sub_county', 'chief_location', 'chief_comments',
                'chief_signature_name', 'chief_date'
            )
        }),
        ('Review', {
            'fields': ('reviewed_at', 'reviewer_comments')
        }),
        ('Timestamps', {
            'fields': ('submitted_at', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def status_badge(self, obj):
# ... (status_badge method remains the same)
        """Display status with color coding"""
        colors = {
            'pending': '#FFA500',
            'under_review': '#2196F3',
            'approved': '#4CAF50',
            'rejected': '#F44336',
        }
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 3px; font-weight: bold;">{}</span>',
            colors.get(obj.status, '#999'),
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    def approve_applications(self, request, queryset):
# ... (approve_applications method remains the same)
        """Bulk approve applications"""
        from django.utils import timezone
        updated = queryset.update(
            status='approved',
            reviewed_at=timezone.now()
        )
        self.message_user(request, f'{updated} application(s) approved.')
    approve_applications.short_description = 'Approve selected applications'
    
    def reject_applications(self, request, queryset):
# ... (reject_applications method remains the same)
        """Bulk reject applications"""
        from django.utils import timezone
        updated = queryset.update(
            status='rejected',
            reviewed_at=timezone.now()
        )
        self.message_user(request, f'{updated} application(s) rejected.')
    reject_applications.short_description = 'Reject selected applications'
    
    def mark_under_review(self, request, queryset):
# ... (mark_under_review method remains the same)
        """Mark applications as under review"""
        updated = queryset.update(status='under_review')
        self.message_user(request, f'{updated} application(s) marked as under review.')
    mark_under_review.short_description = 'Mark as under review'


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
# ... (DocumentAdmin remains the same)
    """Admin interface for Documents"""
    list_display = [
        'application', 'document_type', 'description',
        'file_link', 'uploaded_at'
    ]
    list_filter = ['document_type', 'uploaded_at']
    search_fields = [
        'application__application_number', 'application__student_name',
        'description'
    ]
    readonly_fields = ['uploaded_at']
    
    def file_link(self, obj):
        """Display clickable file link"""
        if obj.file:
            return format_html(
                '<a href="{}" target="_blank">View File</a>',
                obj.file.url
            )
        return '-'
    file_link.short_description = 'File'