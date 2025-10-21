from django.contrib import admin
from django.utils.html import format_html
from .models import UserProfile, BursaryApplication, Document


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """Admin interface for UserProfile"""
    list_display = ['user', 'id_number', 'phone_number', 'county', 'created_at']
    list_filter = ['county', 'created_at']
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
            'fields': ('county', 'sub_county', 'ward', 'village')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


class DocumentInline(admin.TabularInline):
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
        'previous_bursary_recipient', 'submitted_at'
    ]
    search_fields = [
        'application_number', 'student_name', 'institution_name',
        'user_profile__user__email', 'admission_number'
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
                'education_level', 'course_program', 'year_of_study'
            )
        }),
        ('Financial Information', {
            'fields': (
                'annual_family_income', 'tuition_fee', 'amount_requested'
            )
        }),
        ('Family Information', {
            'fields': (
                'family_status', 'number_of_siblings', 'siblings_in_school'
            )
        }),
        ('Parent/Guardian Information', {
            'fields': (
                'parent_guardian_name', 'parent_guardian_phone',
                'parent_guardian_occupation'
            )
        }),
        ('Additional Information', {
            'fields': (
                'reason_for_application', 'previous_bursary_recipient'
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
        """Bulk approve applications"""
        from django.utils import timezone
        updated = queryset.update(
            status='approved',
            reviewed_at=timezone.now()
        )
        self.message_user(request, f'{updated} application(s) approved.')
    approve_applications.short_description = 'Approve selected applications'
    
    def reject_applications(self, request, queryset):
        """Bulk reject applications"""
        from django.utils import timezone
        updated = queryset.update(
            status='rejected',
            reviewed_at=timezone.now()
        )
        self.message_user(request, f'{updated} application(s) rejected.')
    reject_applications.short_description = 'Reject selected applications'
    
    def mark_under_review(self, request, queryset):
        """Mark applications as under review"""
        updated = queryset.update(status='under_review')
        self.message_user(request, f'{updated} application(s) marked as under review.')
    mark_under_review.short_description = 'Mark as under review'


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
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