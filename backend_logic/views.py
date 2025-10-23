from django.views.generic import UpdateView, DetailView # Cleaned up imports
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.urls import reverse_lazy
from django.db import transaction
from django.http import HttpResponseRedirect
from django.shortcuts import render, redirect
from django.contrib.auth.models import User
import logging

logger = logging.getLogger(__name__)

from .models import BursaryApplication, UserProfile, Document
# UserProfileForm removed from imports as it is no longer used
from .forms import MultiStepBursaryApplicationForm, DocumentFormSet, DocumentUploadForm 

def bursary_apply(request):
    """
    Function-Based View to handle the multi-step bursary application form, 
    mapping data from the MultiStepBursaryApplicationForm to User, UserProfile, and BursaryApplication models.
    """
    if request.method == 'POST':
        main_form = MultiStepBursaryApplicationForm(request.POST, request.FILES)
        document_formset = DocumentFormSet(request.POST, request.FILES, prefix='document_formset')
        
        if main_form.is_valid() and document_formset.is_valid():
            try:
                with transaction.atomic():
                    data = main_form.cleaned_data
                    
                    # 1a. Get or Create User and update email/full name
                    username_key = data.get('idNumber') or data.get('email') or data['fullName'].replace(' ', '_')
                    
                    user, created = User.objects.get_or_create(
                        username=username_key, 
                        defaults={
                            'email': data.get('email', f'{username_key}@example.com'),
                            'first_name': data['fullName'].split(' ')[0],
                            'last_name': ' '.join(data['fullName'].split(' ')[1:]) or data['fullName'].split(' ')[0],
                        }
                    )
                    user.email = data.get('email', user.email)
                    user.first_name = data['fullName'].split(' ')[0]
                    user.last_name = ' '.join(data['fullName'].split(' ')[1:]) or data['fullName'].split(' ')[0]
                    user.save()
                    
                    # 1b. Get or Create UserProfile (using data from MultiStepBursaryApplicationForm)
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
                    
                    # 1c. Create BursaryApplication (Mapping form fields to model fields)
                    application = BursaryApplication.objects.create(
                        user_profile=profile,
                        
                        # Student Info
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
                        
                        # Financial Info 
                        annual_family_income=data.get('annual_family_income', 0.00), 
                        tuition_fee=data.get('tuition_fee', 0.00),
                        amount_requested=data.get('amount_requested', 0.00),
                        
                        # Family Info
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
                        
                        # Parent/Guardian Info
                        parent_guardian_name=data.get('guardianName'),
                        parent_guardian_phone=data.get('parentPhone'),
                        parent_guardian_occupation=data.get('fatherOccupation', '') or data.get('motherOccupation', '') or 'N/A', 
                        parent_id_number=data.get('parentId', ''),
                        guardian_relation=data.get('relation', ''),
                        
                        # Additional Info
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
                        
                        # Declaration & Chief Verification
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

                    # --- 2. Process Document Formset and rubberStamp ---
                    document_formset.instance = application
                    documents = document_formset.save(commit=False)
                    
                    # Handle the rubberStamp file from the main form (Step 5)
                    if 'rubberStamp' in request.FILES:
                        Document.objects.create(
                            application=application,
                            document_type='other',
                            file=request.FILES['rubberStamp'],
                            description='Chief Verification Rubber Stamp'
                        )
                    
                    for document in documents:
                        document.save()
                    
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
    model = BursaryApplication
    template_name = 'applications/busary_form.html'
    context_object_name = 'application'

class BursaryUpdateView(LoginRequiredMixin, UpdateView):
    model = BursaryApplication
    form_class = MultiStepBursaryApplicationForm
    template_name = 'applications/busary_form.html'
    
    def get_success_url(self):
        return reverse_lazy('bursary_detail', kwargs={'pk': self.object.pk})

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
                
                # Manual handling of rubberStamp update during form update
                if 'rubberStamp' in self.request.FILES:
                    Document.objects.update_or_create(
                        application=self.object,
                        document_type='other',
                        description='Chief Verification Rubber Stamp',
                        defaults={'file': self.request.FILES['rubberStamp']}
                    )

                for document in documents:
                    document.save()
            else:
                return self.form_invalid(form)

            messages.success(self.request, 'Application updated successfully.')
            return HttpResponseRedirect(self.get_success_url())