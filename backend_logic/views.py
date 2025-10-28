from django.views.generic import UpdateView, DetailView, ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.urls import reverse_lazy
from django.db import transaction
from django.http import HttpResponseRedirect
from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.core.cache import cache
from django.db.models import Prefetch
import logging

logger = logging.getLogger(__name__)

from .models import BursaryApplication, UserProfile, Document
from .forms import MultiStepBursaryApplicationForm, DocumentFormSet


class ApplicationListView(LoginRequiredMixin, ListView):
    """Optimized list view with proper prefetching"""
    model = BursaryApplication
    template_name = 'applications/application_list.html'
    context_object_name = 'applications'
    paginate_by = 20

    def get_queryset(self):
        # Use select_related to avoid N+1 queries
        return BursaryApplication.objects.select_related(
            'user_profile__user'
        ).prefetch_related(
            'documents'  # Prefetch documents if needed in template
        ).order_by('-created_at')


def bursary_apply(request):
    """
    Optimized function-based view for multi-step bursary application form.
    Uses caching and efficient database queries to handle scale.
    """
    if request.method == 'POST':
        main_form = MultiStepBursaryApplicationForm(request.POST, request.FILES)
        document_formset = DocumentFormSet(request.POST, request.FILES, prefix='document_formset')
        
        if main_form.is_valid() and document_formset.is_valid():
            try:
                with transaction.atomic():
                    data = main_form.cleaned_data
                    
                    # Use get_or_create with select_for_update to prevent race conditions
                    username_key = data.get('idNumber') or data.get('email') or data['fullName'].replace(' ', '_')
                    
                    # Try to get existing user first (with locking)
                    user = User.objects.filter(username=username_key).select_for_update().first()
                    
                    if user:
                        # Update existing user
                        user.email = data.get('email', user.email)
                        user.first_name = data['fullName'].split(' ')[0]
                        user.last_name = ' '.join(data['fullName'].split(' ')[1:]) or user.first_name
                        user.save()
                    else:
                        # Create new user
                        user = User.objects.create(
                            username=username_key,
                            email=data.get('email', f'{username_key}@example.com'),
                            first_name=data['fullName'].split(' ')[0],
                            last_name=' '.join(data['fullName'].split(' ')[1:]) or data['fullName'].split(' ')[0]
                        )
                    
                    # Clear email cache if email was checked
                    if data.get('email'):
                        cache.delete(f'email_exists_{data["email"]}')
                    if data.get('idNumber'):
                        cache.delete(f'id_exists_{data["idNumber"]}')
                    
                    # Get or create UserProfile (optimized with update_or_create)
                    profile, created = UserProfile.objects.update_or_create(
                        user=user,
                        defaults={
                            'phone_number': data.get('phone'),
                            'id_number': data.get('idNumber'),
                            'date_of_birth': data.get('dob'),
                            'county': data.get('county'),
                            'sub_county': data.get('subCounty'),
                            'ward': data.get('ward'),
                            'village': data.get('village'),
                            'location': data.get('location', ''),
                            'sub_location': data.get('subLocation', ''),
                        }
                    )
                    
                    # Create BursaryApplication (single bulk insert)
                    application = BursaryApplication.objects.create(
                        user_profile=profile,
                        student_name=data.get('fullName'),
                        institution_name=data.get('institution'),
                        admission_number=data.get('idNumber'),
                        education_level=data.get('level'),
                        course_program=data.get('course'),
                        year_of_study=data.get('yearForm', 1),
                        inst_county=data.get('instCounty', ''),
                        inst_contact=data.get('instContact', ''),
                        term1_score=data.get('term1', ''),
                        term2_score=data.get('term2', ''),
                        term3_score=data.get('term3', ''),
                        annual_family_income=data.get('annual_family_income', 0.00),
                        tuition_fee=data.get('tuition_fee', 0.00),
                        amount_requested=data.get('amount_requested', 0.00),
                        family_status=data.get('family_status', 'pending'),
                        number_of_siblings=data.get('number_of_siblings', 0),
                        siblings_in_school=data.get('siblings_in_school', 0),
                        father_name=data.get('fatherName', ''),
                        mother_name=data.get('motherName', ''),
                        father_occupation=data.get('fatherOccupation', ''),
                        mother_occupation=data.get('motherOccupation', ''),
                        is_single_parent=data.get('singleParent') == 'True',
                        fees_provider=data.get('feesProvider', ''),
                        other_fees_provider=data.get('otherProvider', ''),
                        parent_guardian_name=data.get('guardianName'),
                        parent_guardian_phone=data.get('parentPhone'),
                        parent_guardian_occupation=data.get('fatherOccupation', '') or data.get('motherOccupation', '') or 'N/A',
                        parent_id_number=data.get('parentId', ''),
                        guardian_relation=data.get('relation', ''),
                        reason_for_application=data.get('reason_for_application', 'No reason provided.'),
                        previous_bursary_recipient=data.get('previousBursary') == 'True',
                        cdf_amount=data.get('cdfAmount', 0.00),
                        ministry_amount=data.get('ministryAmount', 0.00),
                        county_gov_amount=data.get('countyGovAmount', 0.00),
                        other_bursary_amount=data.get('otherBursary', 0.00),
                        has_disability=data.get('disability') == 'True',
                        disability_nature=data.get('disabilityNature', ''),
                        disability_reg_no=data.get('disabilityRegNo', ''),
                        is_orphan=data.get('orphan') == 'True',
                        student_signature_name=data.get('signature'),
                        student_declaration_date=data.get('studentDate'),
                        parent_signature_name=data.get('parentSignature'),
                        parent_declaration_date=data.get('parentDate'),
                        chief_full_name=data.get('chiefFullName', ''),
                        chief_sub_location=data.get('chiefSubLocation', ''),
                        chief_county=data.get('chiefCounty', ''),
                        chief_sub_county=data.get('chiefSubCounty', ''),
                        chief_location=data.get('chiefLocation', ''),
                        chief_comments=data.get('chiefComments', ''),
                        chief_signature_name=data.get('chiefSignature', ''),
                        chief_date=data.get('chiefDate', None),
                    )

                    # Process documents - batch creation for efficiency
                    document_formset.instance = application
                    documents = document_formset.save(commit=False)
                    
                    # Collect all documents to bulk create
                    docs_to_create = list(documents)
                    
                    # Add rubber stamp document if present
                    if 'rubberStamp' in request.FILES:
                        docs_to_create.append(
                            Document(
                                application=application,
                                document_type='other',
                                file=request.FILES['rubberStamp'],
                                description='Chief Verification Rubber Stamp'
                            )
                        )
                    
                    # Bulk create all documents in one query
                    if docs_to_create:
                        Document.objects.bulk_create(docs_to_create)
                    
                    messages.success(
                        request,
                        f'Application submitted! Number: {application.application_number}'
                    )
                    return redirect('bursary_success')

            except Exception as e:
                logger.error(f"Bursary application error: {e}", exc_info=True)
                messages.error(request, f'An unexpected error occurred during submission. Error: {str(e)}')
        else:
            messages.error(request, 'Please correct the errors below and try again.')
            # Log form errors for debugging
            logger.warning(f"Form validation errors: {main_form.errors} | Formset errors: {document_formset.errors}")
    else:
        # GET request: initialize forms
        main_form = MultiStepBursaryApplicationForm()
        document_formset = DocumentFormSet(prefix='document_formset')

    context = {
        'form': main_form,
        'document_formset': document_formset,
    }
    return render(request, 'applications/busary_form.html', context)


class BursaryDetailView(DetailView):
    """Optimized detail view with prefetching"""
    model = BursaryApplication
    template_name = 'applications/busary_form.html'
    context_object_name = 'application'
    
    def get_queryset(self):
        # Optimize query with select_related and prefetch_related
        return BursaryApplication.objects.select_related(
            'user_profile__user'
        ).prefetch_related(
            'documents'
        )


class BursaryUpdateView(LoginRequiredMixin, UpdateView):
    """Optimized update view"""
    model = BursaryApplication
    form_class = MultiStepBursaryApplicationForm
    template_name = 'applications/busary_form.html'
    
    def get_success_url(self):
        return reverse_lazy('bursary_detail', kwargs={'pk': self.object.pk})

    def get_queryset(self):
        # Optimize query
        return BursaryApplication.objects.select_related(
            'user_profile__user'
        ).prefetch_related('documents')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['document_formset'] = DocumentFormSet(
                self.request.POST, 
                self.request.FILES, 
                instance=self.object, 
                prefix='document_formset'
            )
        else:
            context['document_formset'] = DocumentFormSet(
                instance=self.object, 
                prefix='document_formset'
            )
        return context
    
    def form_valid(self, form):
        context = self.get_context_data()
        document_formset = context['document_formset']
        
        with transaction.atomic():
            self.object = form.save()
            
            if document_formset.is_valid():
                document_formset.instance = self.object
                documents = document_formset.save(commit=False)
                
                # Handle rubber stamp update
                if 'rubberStamp' in self.request.FILES:
                    Document.objects.update_or_create(
                        application=self.object,
                        document_type='other',
                        description='Chief Verification Rubber Stamp',
                        defaults={'file': self.request.FILES['rubberStamp']}
                    )

                # Bulk create/update documents
                for document in documents:
                    document.save()
            else:
                return self.form_invalid(form)

            messages.success(self.request, 'Application updated successfully.')
            return HttpResponseRedirect(self.get_success_url())