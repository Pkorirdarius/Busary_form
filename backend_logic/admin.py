"""
backend_logic/admin.py - Enhanced with Priority Dashboard and Better Sorting
"""
from django.contrib import admin
from django.utils.html import format_html
from django.db.models import F, Case, When, IntegerField, Q, Count
from django.urls import path
from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import HttpResponse
from django.template.response import TemplateResponse
import csv
from datetime import datetime
from .models import UserProfile, BursaryApplication, Document, ApplicationStatusLog


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """Admin interface for UserProfile"""
    list_display = ['user', 'id_number', 'phone_number', 'county', 'sub_county', 'created_at']
    list_filter = ['county', 'sub_county', 'created_at']
    search_fields = ['user__first_name', 'user__last_name', 'id_number', 'phone_number']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'created_at'
    
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
    """Inline admin for documents with verification status"""
    model = Document
    extra = 0
    readonly_fields = ['uploaded_at', 'file_link', 'file_size']
    fields = ['document_type', 'file_link', 'file_size', 'description', 'status', 'is_verified', 'is_flagged']
    
    def file_link(self, obj):
        if obj.file:
            return format_html('<a href="{}" target="_blank">📄 View</a>', obj.file.url)
        return '-'
    file_link.short_description = 'File'
    
    def file_size(self, obj):
        if obj.file:
            size_mb = obj.file.size / (1024 * 1024)
            return f'{size_mb:.2f} MB'
        return '-'
    file_size.short_description = 'Size'


@admin.register(BursaryApplication)
class EnhancedBursaryApplicationAdmin(admin.ModelAdmin):
    """Enhanced Admin with Priority Dashboard"""
    
    change_list_template = 'admin/bursary_changelist.html'
    
    list_display = [
        'priority_rank', 'application_number', 'student_name', 'need_score_display',
        'education_level', 'amount_requested', 'status_badge', 
        'verification_status_display', 'submitted_at', 'action_buttons'
    ]
    
    list_filter = [
        ('status', admin.ChoicesFieldListFilter),
        ('education_level', admin.ChoicesFieldListFilter),
        'is_verified',
        'is_flagged',
        'is_orphan',
        'has_disability',
        'is_single_parent',
        'previous_bursary_recipient',
        ('submitted_at', admin.DateFieldListFilter),
    ]
    
    search_fields = [
        'application_number', 'student_name', 'institution_name',
        'user_profile__user__email', 'admission_number', 'parent_guardian_name',
        'user_profile__id_number'
    ]
    
    readonly_fields = [
        'application_number', 'submitted_at', 'created_at', 'updated_at',
        'need_score_display', 'financial_summary', 'priority_analysis',
        'document_verification_status'
    ]
    
    inlines = [DocumentInline]
    date_hierarchy = 'submitted_at'
    list_per_page = 25
    
    actions = [
        'approve_applications', 'reject_applications', 'mark_under_review',
        'verify_applications', 'flag_applications', 'unflag_applications',
        'export_priority_list', 'bulk_email_applicants'
    ]
    
    fieldsets = (
        ('Priority & Status', {
            'fields': ('application_number', 'status', 'need_score_display', 
                      'priority_analysis', 'user_profile'),
            'classes': ('wide',)
        }),
        ('Verification & Flags', {
            'fields': ('is_verified', 'verified_by', 'verified_at', 
                      'is_flagged', 'flag_reason', 'document_verification_status'),
        }),
        ('Student Information', {
            'fields': (
                'student_name', 'institution_name', 'admission_number',
                'education_level', 'course_program', 'year_of_study',
                'inst_county', 'inst_contact',
            ),
            'classes': ('collapse',)
        }),
        ('Academic Performance', {
            'fields': ('term1_score', 'term2_score', 'term3_score'),
            'classes': ('collapse',)
        }),
        ('Special Circumstances', {
            'fields': ('is_orphan', 'has_disability', 'disability_nature', 
                      'disability_reg_no', 'is_single_parent'),
            'classes': ('collapse',)
        }),
        ('Financial Information', {
            'fields': ('annual_family_income', 'tuition_fee', 'amount_requested', 
                      'financial_summary'),
        }),
        ('Family Details', {
            'fields': (
                'family_status', 'number_of_siblings', 'siblings_in_school',
                'father_name', 'mother_name', 'father_occupation', 'mother_occupation',
                'parent_guardian_name', 'guardian_relation', 'parent_guardian_phone',
                'parent_guardian_occupation', 'parent_id_number'
            ),
            'classes': ('collapse',)
        }),
        ('Previous Support', {
            'fields': (
                'fees_provider', 'other_fees_provider', 'previous_bursary_recipient',
                'cdf_amount', 'ministry_amount', 'county_gov_amount', 'other_bursary_amount'
            ),
            'classes': ('collapse',)
        }),
        ('Application Details', {
            'fields': ('reason_for_application',),
            'classes': ('collapse',)
        }),
        ('Chief Verification', {
            'fields': (
                'chief_full_name', 'chief_sub_location', 'chief_county',
                'chief_sub_county', 'chief_location', 'chief_comments',
                'chief_signature_name', 'chief_date'
            ),
            'classes': ('collapse',)
        }),
        ('Review & Comments', {
            'fields': ('reviewed_at', 'reviewer_comments'),
        }),
        ('System Timestamps', {
            'fields': ('submitted_at', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        """Enhanced queryset with detailed need score calculation"""
        qs = super().get_queryset(request)
        
        # Detailed need score calculation
        qs = qs.annotate(
            # Income factor (0-15 points)
            income_score=Case(
                When(annual_family_income__lte=30000, then=15),
                When(annual_family_income__lte=50000, then=12),
                When(annual_family_income__lte=100000, then=9),
                When(annual_family_income__lte=200000, then=6),
                When(annual_family_income__lte=300000, then=3),
                default=0,
                output_field=IntegerField()
            ),
            # Sibling factor (0-15 points)
            sibling_score=Case(
                When(siblings_in_school__gte=5, then=15),
                When(siblings_in_school=4, then=12),
                When(siblings_in_school=3, then=9),
                When(siblings_in_school=2, then=6),
                When(siblings_in_school=1, then=3),
                default=0,
                output_field=IntegerField()
            ),
            # Orphan status (0-20 points - highest priority)
            orphan_score=Case(
                When(is_orphan=True, then=20),
                default=0,
                output_field=IntegerField()
            ),
            # Single parent (0-10 points)
            single_parent_score=Case(
                When(is_single_parent=True, then=10),
                default=0,
                output_field=IntegerField()
            ),
            # Disability (0-15 points)
            disability_score=Case(
                When(has_disability=True, then=15),
                default=0,
                output_field=IntegerField()
            ),
            # No previous bursary (0-10 points)
            first_time_score=Case(
                When(previous_bursary_recipient=False, then=10),
                default=0,
                output_field=IntegerField()
            ),
            # Fee burden ratio (0-15 points)
            fee_burden_score=Case(
                When(tuition_fee__gte=F('annual_family_income') * 2, then=15),
                When(tuition_fee__gte=F('annual_family_income'), then=12),
                When(tuition_fee__gte=F('annual_family_income') * 0.5, then=9),
                When(tuition_fee__gte=F('annual_family_income') * 0.3, then=6),
                default=3,
                output_field=IntegerField()
            ),
            # Calculate total need score (max 100 points)
            need_score=F('income_score') + F('sibling_score') + F('orphan_score') + 
                       F('single_parent_score') + F('disability_score') + 
                       F('first_time_score') + F('fee_burden_score')
        )
        
        # Order by: Priority status -> Need score -> Submission date
        return qs.order_by(
            Case(
                When(is_flagged=True, then=2),
                When(status='pending', then=0),
                When(status='under_review', then=1),
                default=3
            ),
            '-need_score',
            'submitted_at'
        )
    
    def changelist_view(self, request, extra_context=None):
        """Add priority statistics to changelist"""
        extra_context = extra_context or {}
        
        # Get statistics
        total = BursaryApplication.objects.count()
        pending = BursaryApplication.objects.filter(status='pending').count()
        under_review = BursaryApplication.objects.filter(status='under_review').count()
        approved = BursaryApplication.objects.filter(status='approved').count()
        rejected = BursaryApplication.objects.filter(status='rejected').count()
        
        # High priority applications (score >= 60)
        high_priority = BursaryApplication.objects.annotate(
            need_score=F('income_score') + F('sibling_score') + F('orphan_score') + 
                       F('single_parent_score') + F('disability_score') + 
                       F('first_time_score') + F('fee_burden_score')
        ).filter(need_score__gte=60, status='pending').count()
        
        flagged = BursaryApplication.objects.filter(is_flagged=True).count()
        unverified = BursaryApplication.objects.filter(is_verified=False, status='pending').count()
        
        extra_context['stats'] = {
            'total': total,
            'pending': pending,
            'under_review': under_review,
            'approved': approved,
            'rejected': rejected,
            'high_priority': high_priority,
            'flagged': flagged,
            'unverified': unverified
        }
        
        return super().changelist_view(request, extra_context)
    
    def priority_rank(self, obj):
        """Show priority rank number"""
        if hasattr(obj, 'need_score'):
            # Get rank based on score
            higher_ranked = BursaryApplication.objects.filter(
                need_score__gt=obj.need_score,
                status='pending'
            ).count()
            return format_html(
                '<span style="background:#006400;color:white;padding:5px 10px;'
                'border-radius:20px;font-weight:bold;">#{}</span>',
                higher_ranked + 1
            )
        return '-'
    priority_rank.short_description = 'Rank'
    priority_rank.admin_order_field = 'need_score'
    
    def need_score_display(self, obj):
        """Enhanced need score display with breakdown"""
        if hasattr(obj, 'need_score'):
            score = obj.need_score
            
            # Color coding with labels
            if score >= 70:
                color = '#dc3545'
                label = 'CRITICAL'
                icon = '🔴'
            elif score >= 55:
                color = '#fd7e14'
                label = 'URGENT'
                icon = '🟠'
            elif score >= 40:
                color = '#ffc107'
                label = 'HIGH'
                icon = '🟡'
            elif score >= 25:
                color = '#17a2b8'
                label = 'MEDIUM'
                icon = '🔵'
            else:
                color = '#28a745'
                label = 'LOW'
                icon = '🟢'
            
            return format_html(
                '<div title="Income: {}, Siblings: {}, Orphan: {}, Single Parent: {}, '
                'Disability: {}, First Time: {}, Fee Burden: {}">'
                '<span style="background-color: {}; color: white; padding: 6px 14px; '
                'border-radius: 6px; font-weight: bold; display: inline-block; '
                'cursor: help;">{} {} ({})</span></div>',
                getattr(obj, 'income_score', 0),
                getattr(obj, 'sibling_score', 0),
                getattr(obj, 'orphan_score', 0),
                getattr(obj, 'single_parent_score', 0),
                getattr(obj, 'disability_score', 0),
                getattr(obj, 'first_time_score', 0),
                getattr(obj, 'fee_burden_score', 0),
                color, icon, score, label
            )
        return '-'
    need_score_display.short_description = 'Priority Score'
    need_score_display.admin_order_field = 'need_score'
    
    def priority_analysis(self, obj):
        """Detailed priority breakdown"""
        if not hasattr(obj, 'need_score'):
            return '-'
        
        breakdown = [
            ('💰 Low Income', getattr(obj, 'income_score', 0), 15),
            ('👨‍👩‍👧‍👦 Siblings in School', getattr(obj, 'sibling_score', 0), 15),
            ('😢 Orphan Status', getattr(obj, 'orphan_score', 0), 20),
            ('👤 Single Parent', getattr(obj, 'single_parent_score', 0), 10),
            ('♿ Disability', getattr(obj, 'disability_score', 0), 15),
            ('🆕 First Time Applicant', getattr(obj, 'first_time_score', 0), 10),
            ('📊 Fee/Income Ratio', getattr(obj, 'fee_burden_score', 0), 15),
        ]
        
        html = '<table style="width:100%; border-collapse: collapse;">'
        html += '<tr style="background:#f8f9fa;"><th style="text-align:left;padding:8px;">Factor</th><th style="padding:8px;">Points</th><th style="padding:8px;">Max</th><th style="padding:8px;">%</th></tr>'
        
        total_earned = 0
        total_max = 0
        
        for label, points, max_points in breakdown:
            percentage = (points / max_points * 100) if max_points > 0 else 0
            total_earned += points
            total_max += max_points
            
            bar_color = '#28a745' if percentage >= 70 else '#ffc107' if percentage >= 40 else '#dc3545'
            
            html += f'''
                <tr style="border-bottom:1px solid #dee2e6;">
                    <td style="padding:8px;">{label}</td>
                    <td style="text-align:center;padding:8px;"><strong>{points}</strong></td>
                    <td style="text-align:center;padding:8px;">{max_points}</td>
                    <td style="padding:8px;">
                        <div style="background:#e9ecef;border-radius:10px;overflow:hidden;height:20px;">
                            <div style="background:{bar_color};width:{percentage}%;height:100%;"></div>
                        </div>
                    </td>
                </tr>
            '''
        
        overall_percentage = (total_earned / total_max * 100) if total_max > 0 else 0
        html += f'''
            <tr style="background:#f8f9fa;font-weight:bold;">
                <td style="padding:8px;">TOTAL</td>
                <td style="text-align:center;padding:8px;">{total_earned}</td>
                <td style="text-align:center;padding:8px;">{total_max}</td>
                <td style="text-align:center;padding:8px;">{overall_percentage:.1f}%</td>
            </tr>
        '''
        html += '</table>'
        
        return format_html(html)
    priority_analysis.short_description = 'Priority Breakdown'
    
    def financial_summary(self, obj):
        """Enhanced financial summary"""
        total_previous_bursary = (
            (obj.cdf_amount or 0) + 
            (obj.ministry_amount or 0) + 
            (obj.county_gov_amount or 0) + 
            (obj.other_bursary_amount or 0)
        )
        
        fee_to_income_ratio = (
            (obj.tuition_fee / obj.annual_family_income * 100) 
            if obj.annual_family_income > 0 else 0
        )
        
        request_percentage = (
            (obj.amount_requested / obj.tuition_fee * 100) 
            if obj.tuition_fee > 0 else 0
        )
        
        return format_html(
            '<div style="background: #f8f9fa; padding: 15px; border-radius: 8px; '
            'border-left: 4px solid #006400;">'
            '<table style="width:100%;">'
            '<tr><td><strong>Annual Family Income:</strong></td>'
            '<td style="text-align:right;">KES {:,.2f}</td></tr>'
            '<tr><td><strong>Total Tuition Fee:</strong></td>'
            '<td style="text-align:right;">KES {:,.2f}</td></tr>'
            '<tr><td><strong>Amount Requested:</strong></td>'
            '<td style="text-align:right;color:#006400;font-weight:bold;">'
            'KES {:,.2f} ({}%)</td></tr>'
            '<tr><td><strong>Previous Bursaries:</strong></td>'
            '<td style="text-align:right;">KES {:,.2f}</td></tr>'
            '<tr style="border-top:2px solid #dee2e6;"><td><strong>Fee/Income Ratio:</strong></td>'
            '<td style="text-align:right;"><span style="background:{};color:white;'
            'padding:3px 8px;border-radius:4px;font-weight:bold;">{:.1f}%</span></td></tr>'
            '</table></div>',
            obj.annual_family_income,
            obj.tuition_fee,
            obj.amount_requested,
            request_percentage,
            total_previous_bursary,
            '#dc3545' if fee_to_income_ratio > 100 else '#ffc107' if fee_to_income_ratio > 50 else '#28a745',
            fee_to_income_ratio
        )
    financial_summary.short_description = 'Financial Summary'
    
    def document_verification_status(self, obj):
        """Show document verification status"""
        docs = obj.documents.all()
        total = docs.count()
        verified = docs.filter(is_verified=True).count()
        flagged = docs.filter(is_flagged=True).count()
        
        if total == 0:
            return format_html('<span style="color:#dc3545;">❌ No documents uploaded</span>')
        
        verification_rate = (verified / total * 100) if total > 0 else 0
        
        color = '#28a745' if verification_rate == 100 else '#ffc107' if verification_rate >= 50 else '#dc3545'
        
        return format_html(
            '<div style="background:#f8f9fa;padding:10px;border-radius:5px;">'
            '<strong>Documents: {}/{} verified ({}%)</strong><br>'
            '<div style="background:#e9ecef;border-radius:10px;overflow:hidden;height:20px;margin:5px 0;">'
            '<div style="background:{};width:{}%;height:100%;"></div></div>'
            '{}</div>',
            verified, total, int(verification_rate),
            color, verification_rate,
            format_html('<span style="color:#dc3545;">⚠️ {} flagged</span>', flagged) if flagged > 0 else ''
        )
    document_verification_status.short_description = 'Document Status'
    
    def verification_status_display(self, obj):
        """Enhanced verification status display"""
        if obj.is_flagged:
            return format_html(
                '<span style="background-color: #dc3545; color: white; padding: 5px 12px; '
                'border-radius: 5px; font-weight: bold; display: inline-block;" '
                'title="{}">🚩 FLAGGED</span>',
                obj.flag_reason or 'No reason provided'
            )
        elif obj.is_verified:
            return format_html(
                '<span style="background-color: #28a745; color: white; padding: 5px 12px; '
                'border-radius: 5px; font-weight: bold; display: inline-block;" '
                'title="Verified by {} on {}">✅ VERIFIED</span>',
                obj.verified_by or 'Unknown',
                obj.verified_at.strftime('%Y-%m-%d %H:%M') if obj.verified_at else 'Unknown date'
            )
        else:
            return format_html(
                '<span style="background-color: #6c757d; color: white; padding: 5px 12px; '
                'border-radius: 5px; font-weight: bold; display: inline-block;">⏳ PENDING</span>'
            )
    verification_status_display.short_description = 'Verification'
    
    def status_badge(self, obj):
        """Enhanced status badge"""
        colors = {
            'pending': '#FFA500',
            'under_review': '#2196F3',
            'approved': '#4CAF50',
            'rejected': '#F44336',
        }
        icons = {
            'pending': '⏳',
            'under_review': '🔍',
            'approved': '✅',
            'rejected': '❌',
        }
        return format_html(
            '<span style="background-color: {}; color: white; padding: 5px 12px; '
            'border-radius: 5px; font-weight: bold; display: inline-block;">{} {}</span>',
            colors.get(obj.status, '#999'),
            icons.get(obj.status, ''),
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    def action_buttons(self, obj):
        """Quick action buttons"""
        return format_html(
            '<a class="button" href="/admin/backend_logic/bursaryapplication/{}/change/" '
            'style="background:#2196F3;color:white;padding:5px 10px;text-decoration:none;'
            'border-radius:4px;margin:2px;">View</a>'
            '<a class="button" href="/analytics/timeline/{}/" target="_blank" '
            'style="background:#28a745;color:white;padding:5px 10px;text-decoration:none;'
            'border-radius:4px;margin:2px;">Timeline</a>',
            obj.pk, obj.pk
        )
    action_buttons.short_description = 'Actions'
    
    # === ADMIN ACTIONS ===
    
    def export_priority_list(self, request, queryset):
        """Export priority-sorted list as CSV"""
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="priority_list_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv"'
        
        writer = csv.writer(response)
        writer.writerow([
            'Rank', 'Application Number', 'Student Name', 'Priority Score',
            'Status', 'Education Level', 'Amount Requested', 'Tuition Fee',
            'Annual Income', 'Orphan', 'Disability', 'Siblings in School',
            'Fee/Income Ratio', 'Submitted Date'
        ])
        
        for rank, app in enumerate(queryset, 1):
            writer.writerow([
                rank,
                app.application_number,
                app.student_name,
                getattr(app, 'need_score', 0),
                app.get_status_display(),
                app.get_education_level_display(),
                app.amount_requested,
                app.tuition_fee,
                app.annual_family_income,
                'Yes' if app.is_orphan else 'No',
                'Yes' if app.has_disability else 'No',
                app.siblings_in_school,
                f'{(app.tuition_fee / app.annual_family_income * 100):.1f}%' if app.annual_family_income > 0 else 'N/A',
                app.submitted_at.strftime('%Y-%m-%d')
            ])
        
        self.message_user(request, f'Exported {queryset.count()} applications', messages.SUCCESS)
        return response
    export_priority_list.short_description = '📊 Export Priority List (CSV)'


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    """Enhanced Document Admin"""
    list_display = [
        'application', 'document_type', 'description',
        'file_link', 'file_size', 'status_badge', 'uploaded_at'
    ]
    list_filter = ['document_type', 'status', 'is_verified', 'is_flagged', 'uploaded_at']
    search_fields = ['application__application_number', 'application__student_name', 'description']
    readonly_fields = ['uploaded_at', 'file_size']
    
    actions = ['verify_documents', 'flag_documents']
    
    def file_link(self, obj):
        if obj.file:
            return format_html(
                '<a href="{}" target="_blank" style="background:#2196F3;color:white;'
                'padding:5px 10px;text-decoration:none;border-radius:4px;">📄 View</a>',
                obj.file.url
            )
        return '-'
    file_link.short_description = 'File'
    
    def file_size(self, obj):
        if obj.file:
            size_mb = obj.file.size / (1024 * 1024)
            return f'{size_mb:.2f} MB'
        return '-'
    file_size.short_description = 'Size'
    
    def status_badge(self, obj):
        colors = {
            'pending': '#ffc107',
            'verified': '#28a745',
            'rejected': '#dc3545'
        }
        return format_html(
            '<span style="background:{};color:white;padding:5px 10px;'
            'border-radius:5px;font-weight:bold;">{}</span>',
            colors.get(obj.status, '#6c757d'),
            obj.get_status_display() if hasattr(obj, 'get_status_display') else obj.status.upper()
        )
    status_badge.short_description = 'Status'


@admin.register(ApplicationStatusLog)
class StatusLogAdmin(admin.ModelAdmin):
    """Status log admin"""
    list_display = ['application', 'old_status', 'new_status', 'changed_at']
    list_filter = ['new_status', 'changed_at']
    search_fields = ['application__application_number', 'application__student_name']
    readonly_fields = ['application', 'old_status', 'new_status', 'comments', 'changed_at']
    date_hierarchy = 'changed_at'
    
    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False