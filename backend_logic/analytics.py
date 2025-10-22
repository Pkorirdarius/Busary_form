from django.shortcuts import render
from django.contrib.auth.decorators import login_required, permission_required
from django.db.models import Count, Sum, Avg, Q, F
from django.db.models.functions import TruncDate, TruncMonth
from django.utils import timezone
from datetime import timedelta
from .models import BursaryApplication


@login_required
@permission_required('applications.view_analytics', raise_exception=True)
def analytics_dashboard(request):
    """
    Main analytics dashboard showing key metrics and trends
    """
    # Get date range (default: last 30 days)
    days = int(request.GET.get('days', 30))
    start_date = timezone.now() - timedelta(days=days)
    
    # Overall Statistics
    total_applications = BursaryApplication.objects.count()
    pending_count = BursaryApplication.objects.filter(status='pending').count()
    approved_count = BursaryApplication.objects.filter(status='approved').count()
    rejected_count = BursaryApplication.objects.filter(status='rejected').count()
    under_review_count = BursaryApplication.objects.filter(status='under_review').count()
    
    # Financial Statistics
    financial_stats = BursaryApplication.objects.aggregate(
        total_requested=Sum('amount_requested'),
        total_approved=Sum('amount_requested', filter=Q(status='approved')),
        avg_requested=Avg('amount_requested'),
        avg_family_income=Avg('annual_family_income'),
    )
    
    # Applications by Status (for pie chart)
    status_distribution = BursaryApplication.objects.values('status').annotate(
        count=Count('id')
    ).order_by('-count')
    
    # Applications over time (for line chart)
    applications_by_date = BursaryApplication.objects.filter(
        created_at__gte=start_date
    ).annotate(
        date=TruncDate('created_at')
    ).values('date').annotate(
        count=Count('id')
    ).order_by('date')
    
    # Applications by education level
    by_education_level = BursaryApplication.objects.values('education_level').annotate(
        count=Count('id'),
        total_amount=Sum('amount_requested')
    ).order_by('-count')
    
    # Applications by county (top 10)
    by_county = BursaryApplication.objects.values(
        'user_profile__county'
    ).annotate(
        count=Count('id')
    ).order_by('-count')[:10]
    
    # Average processing time
    approved_apps = BursaryApplication.objects.filter(
        status='approved',
        reviewed_at__isnull=False
    )
    
    avg_processing_days = 0
    if approved_apps.exists():
        processing_times = [
            (app.reviewed_at - app.submitted_at).days 
            for app in approved_apps
        ]
        avg_processing_days = sum(processing_times) / len(processing_times)
    
    # Recent status changes
    recent_changes = ApplicationStatusLog.objects.select_related(
        'application', 'changed_by'
    ).order_by('-changed_at')[:10]
    
    # Applications by family status
    by_family_status = BursaryApplication.objects.values('family_status').annotate(
        count=Count('id')
    ).order_by('-count')
    
    # Monthly trends (last 6 months)
    six_months_ago = timezone.now() - timedelta(days=180)
    monthly_trends = BursaryApplication.objects.filter(
        created_at__gte=six_months_ago
    ).annotate(
        month=TruncMonth('created_at')
    ).values('month').annotate(
        total=Count('id'),
        approved=Count('id', filter=Q(status='approved')),
        rejected=Count('id', filter=Q(status='rejected')),
    ).order_by('month')
    
    # Top requesters (by amount)
    top_requests = BursaryApplication.objects.select_related(
        'user_profile__user'
    ).order_by('-amount_requested')[:10]
    
    # Approval rate
    approval_rate = 0
    if total_applications > 0:
        approval_rate = (approved_count / total_applications) * 100
    
    context = {
        'total_applications': total_applications,
        'pending_count': pending_count,
        'approved_count': approved_count,
        'rejected_count': rejected_count,
        'under_review_count': under_review_count,
        'financial_stats': financial_stats,
        'status_distribution': status_distribution,
        'applications_by_date': applications_by_date,
        'by_education_level': by_education_level,
        'by_county': by_county,
        'avg_processing_days': round(avg_processing_days, 1),
        'recent_changes': recent_changes,
        'by_family_status': by_family_status,
        'monthly_trends': monthly_trends,
        'top_requests': top_requests,
        'approval_rate': round(approval_rate, 1),
        'days': days,
    }
    
    return render(request, 'applications/analytics_dashboard.html', context)


@login_required
@permission_required('applications.view_analytics', raise_exception=True)
def export_analytics_csv(request):
    """
    Export analytics data as CSV
    """
    import csv
    from django.http import HttpResponse
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="bursary_analytics.csv"'
    
    writer = csv.writer(response)
    writer.writerow([
        'Application Number', 'Student Name', 'Status', 'Amount Requested',
        'Tuition Fee', 'Education Level', 'County', 'Submitted Date',
        'Reviewed Date', 'Days to Review'
    ])
    
    applications = BursaryApplication.objects.select_related(
        'user_profile'
    ).all()
    
    for app in applications:
        days_to_review = ''
        if app.reviewed_at:
            days_to_review = (app.reviewed_at - app.submitted_at).days
        
        writer.writerow([
            app.application_number,
            app.student_name,
            app.get_status_display(),
            app.amount_requested,
            app.tuition_fee,
            app.get_education_level_display(),
            app.user_profile.county,
            app.submitted_at.strftime('%Y-%m-%d'),
            app.reviewed_at.strftime('%Y-%m-%d') if app.reviewed_at else '',
            days_to_review
        ])
    
    return response


@login_required
@permission_required('applications.view_analytics', raise_exception=True)
def application_timeline(request, pk):
    """
    View detailed timeline of an application's status changes
    """
    application = BursaryApplication.objects.get(pk=pk)
    timeline = ApplicationStatusLog.objects.filter(
        application=application
    ).select_related('changed_by').order_by('changed_at')
    
    context = {
        'application': application,
        'timeline': timeline,
    }
    
    return render(request, 'applications/application_timeline.html', context)