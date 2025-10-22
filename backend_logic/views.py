from django.views.generic import TemplateView, CreateView, UpdateView, DetailView, ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.urls import reverse_lazy
from django.db import transaction
from django.http import HttpResponseRedirect
from django.shortcuts import render, redirect

from .models import BursaryApplication, UserProfile, Document
from .forms import BursaryApplicationForm, UserProfileForm, DocumentFormSet

class BursaryCreateView(CreateView):
    """
    Class-Based View for creating a new bursary application.
    Handles form rendering, validation, and submission.
    """
    model = BursaryApplication
    form_class = BursaryApplicationForm
    template_name = 'applications/busary_form.html'
    success_url = reverse_lazy('bursary_success')

    def get_context_data(self, **kwargs):
        """Add document formset and profile form to context"""
        context = super().get_context_data(**kwargs)
        
        if self.request.POST:
            context['profile_form'] = UserProfileForm(self.request.POST)
            context['document_formset'] = DocumentFormSet(
                self.request.POST,
                self.request.FILES
            )
        else:
            context['profile_form'] = UserProfileForm()
            context['document_formset'] = DocumentFormSet()
        
        return context

    def form_valid(self, form):
        """
        Handle form submission with profile and documents.
        Uses transaction to ensure data consistency.
        """
        context = self.get_context_data()
        profile_form = context['profile_form']
        document_formset = context['document_formset']

        # Validate all forms
        if not (profile_form.is_valid() and document_formset.is_valid()):
            return self.form_invalid(form)

        try:
            with transaction.atomic():
                # Create or get user
                from django.contrib.auth.models import User
                user, created = User.objects.get_or_create(
                    email=profile_form.cleaned_data['email'],
                    defaults={
                        'username': profile_form.cleaned_data['email'],
                        'first_name': profile_form.cleaned_data['first_name'],
                        'last_name': profile_form.cleaned_data['last_name'],
                    }
                )

                # Create or update user profile
                profile, created = UserProfile.objects.update_or_create(
                    user=user,
                    defaults={
                        'phone_number': profile_form.cleaned_data['phone_number'],
                        'id_number': profile_form.cleaned_data['id_number'],
                        'date_of_birth': profile_form.cleaned_data['date_of_birth'],
                        'county': profile_form.cleaned_data['county'],
                        'sub_county': profile_form.cleaned_data['sub_county'],
                        'ward': profile_form.cleaned_data['ward'],
                        'village': profile_form.cleaned_data['village'],
                    }
                )

                # Save the application
                application = form.save(commit=False)
                application.user_profile = profile
                application.save()

                # Save documents
                document_formset.instance = application
                document_formset.save()

                messages.success(
                    self.request,
                    f'Application submitted successfully! Your application number is: {application.application_number}'
                )

                return HttpResponseRedirect(self.get_success_url())

        except Exception as e:
            messages.error(
                self.request,
                f'An error occurred while submitting your application: {str(e)}'
            )
            return self.form_invalid(form)

    def form_invalid(self, form):
        """Handle invalid form submission"""
        messages.error(
            self.request,
            'Please correct the errors below and try again.'
        )
        return super().form_invalid(form)


class BursaryUpdateView(LoginRequiredMixin, UpdateView):
    """View for updating an existing bursary application"""
    model = BursaryApplication
    form_class = BursaryApplicationForm
    template_name = 'applications/busary_form.html'
    success_url = reverse_lazy('bursary_success')

    def get_queryset(self):
        """Ensure users can only edit their own applications"""
        return BursaryApplication.objects.filter(
            user_profile__user=self.request.user,
            status='pending'  # Only allow editing pending applications
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        if self.request.POST:
            context['document_formset'] = DocumentFormSet(
                self.request.POST,
                self.request.FILES,
                instance=self.object
            )
        else:
            context['document_formset'] = DocumentFormSet(instance=self.object)
        
        context['is_update'] = True
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        document_formset = context['document_formset']

        if document_formset.is_valid():
            with transaction.atomic():
                self.object = form.save()
                document_formset.instance = self.object
                document_formset.save()
                
                messages.success(
                    self.request,
                    'Application updated successfully!'
                )
                return HttpResponseRedirect(self.get_success_url())
        else:
            return self.form_invalid(form)


class BursaryDetailView(DetailView):
    """View for displaying application details"""
    model = BursaryApplication
    template_name = 'applications/busary_form.html'
    context_object_name = 'application'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['documents'] = self.object.documents.all()
        return context


class ApplicationListView(LoginRequiredMixin, ListView):
    """View for listing user's applications"""
    model = BursaryApplication
    template_name = 'applications/application_list.html'
    context_object_name = 'applications'
    paginate_by = 10

    def get_queryset(self):
        """Return applications for the current user"""
        return BursaryApplication.objects.filter(
            user_profile__user=self.request.user
        ).order_by('-submitted_at')


class ApplicationSuccessView(DetailView):
    """Success page after application submission"""
    template_name = 'applications/busary_form.html'

    def get(self, request, *args, **kwargs):
        """Display success message"""
        return render(request, self.template_name)


# Function-based view alternative for simple form rendering
def bursary_application_view(request):
    """
    Function-based view alternative for handling bursary applications.
    Can be used instead of BursaryCreateView if preferred.
    """
    if request.method == 'POST':
        application_form = BursaryApplicationForm(request.POST)
        profile_form = UserProfileForm(request.POST)
        document_formset = DocumentFormSet(request.POST, request.FILES)

        if (application_form.is_valid() and 
            profile_form.is_valid() and 
            document_formset.is_valid()):
            
            try:
                with transaction.atomic():
                    # Create user and profile
                    from django.contrib.auth.models import User
                    user, created = User.objects.get_or_create(
                        email=profile_form.cleaned_data['email'],
                        defaults={
                            'username': profile_form.cleaned_data['email'],
                            'first_name': profile_form.cleaned_data['first_name'],
                            'last_name': profile_form.cleaned_data['last_name'],
                        }
                    )

                    profile, created = UserProfile.objects.update_or_create(
                        user=user,
                        defaults={
                            'phone_number': profile_form.cleaned_data['phone_number'],
                            'id_number': profile_form.cleaned_data['id_number'],
                            'date_of_birth': profile_form.cleaned_data['date_of_birth'],
                            'county': profile_form.cleaned_data['county'],
                            'sub_county': profile_form.cleaned_data['sub_county'],
                            'ward': profile_form.cleaned_data['ward'],
                            'village': profile_form.cleaned_data['village'],
                        }
                    )

                    # Save application
                    application = application_form.save(commit=False)
                    application.user_profile = profile
                    application.save()

                    # Save documents
                    document_formset.instance = application
                    document_formset.save()

                    messages.success(
                        request,
                        f'Application submitted! Number: {application.application_number}'
                    )
                    return redirect('bursary_success')

            except Exception as e:
                messages.error(request, f'Error: {str(e)}')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        application_form = BursaryApplicationForm()
        profile_form = UserProfileForm()
        document_formset = DocumentFormSet()

    context = {
        'form': application_form,
        'profile_form': profile_form,
        'document_formset': document_formset,
    }
    return render(request, 'applications/bursary_form.html', context)