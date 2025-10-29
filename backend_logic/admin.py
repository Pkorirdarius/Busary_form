from django.contrib import admin
from django.utils.html import format_html
from django.db.models import F, Case, When, IntegerField, DecimalField, Value
from django.db.models.functions import Coalesce
from django.urls import path
from django.shortcuts import render, redirect
from django.contrib import messages
from .models import UserProfile, BursaryApplication, Document


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """Admin interface for UserProfile"""
    list_display = ['user', 'id_number', 'phone_number', 'county', 'sub_county', 'location', 'created_at']
    list_filter = ['county', 'sub_county', 'created_at']
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
            'fields': ('county', 'sub_county', 'ward', 'location', 'sub_location', 'village')
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
    """Enhanced Admin interface for BursaryApplication with need-based sorting and verification"""
    
    list_display = [
        'application_number', 'student_name', 'need_score_display',
        'education_level', 'amount_requested', 'status_badge', 
        'verification_status_display', 'submitted_at'
    ]
    
    list_filter = [
        'status', 'education_level', 'family_status',
        'previous_bursary_recipient', 'submitted_at', 'is_orphan',
        'has_disability', 'is_verified', 'is_flagged',
    ]
    
    search_fields = [
        'application_number', 'student_name', 'institution_name',
        'user_profile__user__email', 'admission_number', 'parent_guardian_name'
    ]
    
    readonly_fields = [
        'application_number', 'submitted_at', 'created_at', 'updated_at',
        'need_score_display', 'financial_summary'
    ]
    
    inlines = [DocumentInline]
    date_hierarchy = 'submitted_at'
    
    actions = [
        'approve_applications', 'reject_applications', 'mark_under_review',
        'verify_applications', 'flag_applications', 'unflag_applications',
        'sort_by_need'
    ]
    
    fieldsets = (
        ('Application Info', {
            'fields': ('application_number', 'user_profile', 'status', 'need_score_display')
        }),
        ('Verification & Flags', {
            'fields': ('is_verified', 'is_flagged', 'flag_reason', 'verified_by', 'verified_at'),
            'classes': ('collapse',)
        }),
        ('Student Information', {
            'fields': (
                'student_name', 'institution_name', 'admission_number',
                'education_level', 'course_program', 'year_of_study',
                'inst_county', 'inst_contact',
            )
        }),
        ('School Performance', {
            'fields': ('term1_score', 'term2_score', 'term3_score')
        }),
        ('Disability Status', {
            'fields': ('has_disability', 'disability_nature', 'disability_reg_no', 'is_orphan')
        }),
        ('Financial Information', {
            'fields': (
                'annual_family_income', 'tuition_fee', 'amount_requested', 'financial_summary'
            )
        }),
        ('Family Information', {
            'fields': (
                'family_status', 'number_of_siblings', 'siblings_in_school',
                'father_name', 'mother_name', 'father_occupation', 'mother_occupation',
                'is_single_parent',
            )
        }),
        ('Parent/Guardian Information', {
            'fields': (
                'parent_guardian_name', 'guardian_relation', 'parent_guardian_phone',
                'parent_guardian_occupation', 'parent_id_number'
            )
        }),
        ('Financial Support & Bursary History', {
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
        ('Declaration & Chief Verification', {
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
    
    def get_queryset(self, request):
        """Override queryset to add need score calculation"""
        qs = super().get_queryset(request)
        
        # Calculate need score based on multiple factors
        qs = qs.annotate(
            # Income factor (lower income = higher need)
            income_score=Case(
                When(annual_family_income__lte=50000, then=Value(10)),
                When(annual_family_income__lte=100000, then=Value(8)),
                When(annual_family_income__lte=200000, then=Value(6)),
                When(annual_family_income__lte=300000, then=Value(4)),
                default=Value(2),
                output_field=IntegerField()
            ),
            # Sibling factor (more siblings in school = higher need)
            sibling_score=Case(
                When(siblings_in_school__gte=4, then=Value(10)),
                When(siblings_in_school=3, then=Value(8)),
                When(siblings_in_school=2, then=Value(6)),
                When(siblings_in_school=1, then=Value(4)),
                default=Value(0),
                output_field=IntegerField()
            ),
            # Orphan factor
            orphan_score=Case(
                When(is_orphan=True, then=Value(10)),
                default=Value(0),
                output_field=IntegerField()
            ),
            # Single parent factor
            single_parent_score=Case(
                When(is_single_parent=True, then=Value(5)),
                default=Value(0),
                output_field=IntegerField()
            ),
            # Disability factor
            disability_score=Case(
                When(has_disability=True, then=Value(5)),
                default=Value(0),
                output_field=IntegerField()
            ),
            # Previous bursary factor (no previous bursary = higher need)
            previous_bursary_score=Case(
                When(previous_bursary_recipient=False, then=Value(5)),
                default=Value(0),
                output_field=IntegerField()
            ),
            # Fee burden factor (higher fee relative to income = higher need)
            fee_burden_score=Case(
                When(tuition_fee__gte=F('annual_family_income'), then=Value(10)),
                When(tuition_fee__gte=F('annual_family_income') * 0.5, then=Value(8)),
                When(tuition_fee__gte=F('annual_family_income') * 0.3, then=Value(6)),
                default=Value(3),
                output_field=IntegerField()
            ),
            # Total need score
            need_score=F('income_score') + F('sibling_score') + F('orphan_score') + 
                       F('single_parent_score') + F('disability_score') + 
                       F('previous_bursary_score') + F('fee_burden_score')
        )
        
        # Default ordering: highest need first, then by submission date
        return qs.order_by('-need_score', '-submitted_at')
    
    def need_score_display(self, obj):
        """Display the calculated need score"""
        if hasattr(obj, 'need_score'):
            score = obj.need_score
            # Color code based on need level
            if score >= 40:
                color = '#dc3545'  # Red - High need
                label = 'URGENT'
            elif score >= 30:
                color = '#fd7e14'  # Orange - Medium-high need
                label = 'HIGH'
            elif score >= 20:
                color = '#ffc107'  # Yellow - Medium need
                label = 'MEDIUM'
            else:
                color = '#28a745'  # Green - Lower need
                label = 'LOW'
            
            return format_html(
                '<span style="background-color: {}; color: white; padding: 5px 12px; '
                'border-radius: 5px; font-weight: bold; display: inline-block;">'
                '{} ({})</span>',
                color, score, label
            )
        return '-'
    need_score_display.short_description = 'Need Score'
    need_score_display.admin_order_field = 'need_score'
    
    def financial_summary(self, obj):
        """Display financial summary for quick review"""
        total_bursary = (obj.cdf_amount or 0) + (obj.ministry_amount or 0) + \
                       (obj.county_gov_amount or 0) + (obj.other_bursary_amount or 0)
        
        return format_html(
            '<div style="background: #f8f9fa; padding: 10px; border-radius: 5px;">'
            '<strong>Family Income:</strong> KES {:,.2f}/year<br>'
            '<strong>Tuition Fee:</strong> KES {:,.2f}<br>'
            '<strong>Requested:</strong> KES {:,.2f}<br>'
            '<strong>Previous Bursaries:</strong> KES {:,.2f}<br>'
            '<strong>Fee/Income Ratio:</strong> {:.1%}'
            '</div>',
            obj.annual_family_income,
            obj.tuition_fee,
            obj.amount_requested,
            total_bursary,
            obj.tuition_fee / obj.annual_family_income if obj.annual_family_income > 0 else 0
        )
    financial_summary.short_description = 'Financial Summary'
    
    def verification_status_display(self, obj):
        """Display verification status with color coding"""
        if obj.is_flagged:
            return format_html(
                '<span style="background-color: #dc3545; color: white; padding: 3px 10px; '
                'border-radius: 3px; font-weight: bold;">🚩 FLAGGED</span>'
            )
        elif obj.is_verified:
            return format_html(
                '<span style="background-color: #28a745; color: white; padding: 3px 10px; '
                'border-radius: 3px; font-weight: bold;">✓ VERIFIED</span>'
            )
        else:
            return format_html(
                '<span style="background-color: #6c757d; color: white; padding: 3px 10px; '
                'border-radius: 3px; font-weight: bold;">⏳ PENDING</span>'
            )
    verification_status_display.short_description = 'Verification'
    
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
    
    # === ADMIN ACTIONS ===
    
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
    
    def verify_applications(self, request, queryset):
        """Verify selected applications"""
        from django.utils import timezone
        updated = queryset.update(
            is_verified=True,
            is_flagged=False,
            verified_by=request.user.username,
            verified_at=timezone.now()
        )
        self.message_user(request, f'{updated} application(s) verified.', messages.SUCCESS)
    verify_applications.short_description = '✓ Verify selected applications'
    
    def flag_applications(self, request, queryset):
        """Flag applications for review"""
        if 'apply' in request.POST:
            reason = request.POST.get('flag_reason', '')
            updated = queryset.update(
                is_flagged=True,
                flag_reason=reason
            )
            self.message_user(request, f'{updated} application(s) flagged.', messages.WARNING)
            return redirect('.')
        
        return render(request, 'admin/flag_applications.html', {
            'applications': queryset,
            'action_name': 'flag_applications'
        })
    flag_applications.short_description = '🚩 Flag selected applications'
    
    def unflag_applications(self, request, queryset):
        """Remove flags from applications"""
        updated = queryset.update(
            is_flagged=False,
            flag_reason=''
        )
        self.message_user(request, f'{updated} application(s) unflagged.', messages.SUCCESS)
    unflag_applications.short_description = 'Remove flags from selected'
    
    def sort_by_need(self, request, queryset):
        """Sort and display applications by need score"""
        # This action redirects to a custom view showing sorted results
        self.message_user(
            request, 
            'Applications are automatically sorted by need score (highest need first). '
            'The "Need Score" column shows the calculated priority.',
            messages.INFO
        )
    sort_by_need.short_description = '📊 View need-based priority'


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