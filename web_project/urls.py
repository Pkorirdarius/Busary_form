"""
URL configuration for web_project project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from backend_logic import views, analytics

urlpatterns = [
    path('admin/', admin.site.urls),
    # Main landing page
    path('', views.HomeView.as_view(), name='home'),
    
    # Application routes
    path('application/apply/', views.BursaryCreateView.as_view(), name='bursary_apply'),
    path('application/<int:pk>/', views.BursaryDetailView.as_view(), name='bursary_detail'),
    path('application/<int:pk>/edit/', views.BursaryUpdateView.as_view(), name='bursary_update'),
    path('application/success/', views.ApplicationSuccessView.as_view(), name='application_success'),
    path('applications/', views.ApplicationListView.as_view(), name='application_list'),
    
    # Analytics routes (admin only)
    path('analytics/', analytics.analytics_dashboard, name='analytics_dashboard'),
    path('analytics/export/', analytics.export_analytics_csv, name='export_analytics'),
    path('analytics/timeline/<int:pk>/', analytics.application_timeline, name='application_timeline'),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
