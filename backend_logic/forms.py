from django import forms
from .models import UserProfile, BursaryApplication, Document
from django.core.exceptions import ValidationError

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['phone', 'id_number', 'county', 'ward', 'location']


class BursaryApplicationForm(forms.ModelForm):
    class Meta:
        model = BursaryApplication
        fields = [
            'institution_name', 'tuition_fee', 'amount_requested',
            'siblings_total', 'siblings_in_school', 'family_income', 'reason_for_application'
        ]

    def clean(self):
        cleaned_data = super().clean()
        tuition_fee = cleaned_data.get('tuition_fee')
        amount_requested = cleaned_data.get('amount_requested')
        siblings_total = cleaned_data.get('siblings_total')
        siblings_in_school = cleaned_data.get('siblings_in_school')
        income = cleaned_data.get('family_income')

        if amount_requested and tuition_fee and amount_requested > tuition_fee:
            raise ValidationError("Requested amount cannot exceed tuition fee.")
        if siblings_total is not None and siblings_in_school is not None and siblings_in_school > siblings_total:
            raise ValidationError("Siblings in school cannot exceed total siblings.")
        if income and (income < 0 or income > 5000000):
            raise ValidationError("Please enter a reasonable family income.")


class DocumentForm(forms.ModelForm):
    class Meta:
        model = Document
        fields = ['file']

    def clean_file(self):
        file = self.cleaned_data.get('file')
        if file.size > 5 * 1024 * 1024:
            raise ValidationError("File size exceeds 5MB.")
        if not file.name.lower().endswith(('.pdf', '.jpg', '.jpeg', '.png')):
            raise ValidationError("Only PDF or image files are allowed.")
        return file


DocumentFormSet = forms.modelformset_factory(Document, form=DocumentForm, extra=2)
