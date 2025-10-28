from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView
from backend_logic import analytics # Assumes analytics views are in backend_logic/analytics.py

urlpatterns = [
    # Django Admin Interface
    path('admin/', admin.site.urls),
    
    # Application Routes (All /bursary/... URLs are handled by backend_logic.urls)
    path('bursary/', include('backend_logic.urls')), 
    
    # Root Redirect: Redirects '/' to '/bursary/apply/'
    path('', RedirectView.as_view(pattern_name='bursary_apply', permanent=False), name='home'),
    
    # Analytics Routes (Admin access likely required)
    path('analytics/', analytics.analytics_dashboard, name='analytics_dashboard'),
    path('analytics/export/', analytics.export_analytics_csv, name='export_analytics'),
    path('analytics/timeline/<int:pk>/', analytics.application_timeline, name='application_timeline'),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
if settings.DEBUG:
# This must be included in your root urlpatterns to define the 'djdt' namespace
    urlpatterns += [
        path('__debug__/', include('debug_toolbar.urls')),
    ]
