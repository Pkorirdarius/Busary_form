from django.urls import path
from .views import (
    BursaryCreateView,
    BursaryDetailView,
    BursaryUpdateView,
)
from django.views.generic import TemplateView

urlpatterns = [
    path('apply/', BursaryCreateView.as_view(), name='bursary_apply'),
    path('<int:pk>/', BursaryDetailView.as_view(), name='bursary_detail'),
    path('<int:pk>/edit/', BursaryUpdateView.as_view(), name='bursary_update'),
    path('success/', TemplateView.as_view(template_name="applications/success.html"), name='bursary_success'),
]
