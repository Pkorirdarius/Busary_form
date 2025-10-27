from django.urls import path
from .views import (
    bursary_apply, # UPDATED: Changed from BursaryCreateView.as_view() to the function-based view
    BursaryDetailView,
    BursaryUpdateView,
    ApplicationListView,
)
from django.views.generic import TemplateView

urlpatterns = [
    path('', ApplicationListView.as_view(), name='application_list'),
    # The 'bursary_apply' path now points to the function-based view
    path('apply/', bursary_apply, name='bursary_apply'), 
    path('<int:pk>/', BursaryDetailView.as_view(), name='bursary_detail'),
    path('<int:pk>/edit/', BursaryUpdateView.as_view(), name='bursary_update'),
    path('success/', TemplateView.as_view(template_name="applications/application_success.html"), name='bursary_success'),
]
