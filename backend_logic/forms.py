from django import forms
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
from .models import UserProfile, BursaryApplication, Document
from django.contrib.auth.models import User
from datetime import date


class UserProfileForm(forms.ModelForm):
    """Form for user profile information"""
    first_name = forms.CharField(max_length=150, required=True)
    last_name = forms.CharField(max_length=150, required=True)
    email = forms.EmailField(required=True)

    class Meta:
        model = UserProfile
        fields = ['phone_number', 'id_number', 'date_of_birth', 'county', 
                  'sub_county', 'ward', 'village']
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
            'phone_number': forms.TextInput(attrs={'placeholder': '+254712345678'}),
            'id_number': forms.TextInput(attrs={'placeholder': 'National ID Number'}),
        }

    def clean_email(self):
        """Validate email is not already in use by another user"""
        email = self.cleaned_data.get('email')
        if email:
            # Check if editing existing user
            if hasattr(self, 'instance') and self.instance.pk:
                # Exclude current user from duplicate check
                if User.objects.filter(email=email).exclude(
                    pk=self.instance.user.pk
                ).exists():
                    raise ValidationError(
                        "This email address is already registered."
                    )
            else:
                # New user - check if email exists
                if User.objects.filter(email=email).exists():
                    raise ValidationError(
                        "This email address is already registered."
                    )
        return email

    def clean_id_number(self):
        """Validate ID number format and uniqueness"""
        id_number = self.cleaned_data.get('id_number')
        if id_number:
            # Remove spaces and convert to string
            id_number = str(id_number).strip().replace(' ', '')
            
            # Check length (Kenyan ID is typically 7-8 digits)
            if len(id_number) < 7 or len(id_number) > 9:
                raise ValidationError(
                    "ID number must be between 7 and 9 digits."
                )
            
            # Check if numeric
            if not id_number.isdigit():
                raise ValidationError(
                    "ID number must contain only digits."
                )
            
            # Check uniqueness
            if hasattr(self, 'instance') and self.instance.pk:
                if UserProfile.objects.filter(id_number=id_number).exclude(
                    pk=self.instance.pk
                ).exists():
                    raise ValidationError(
                        "This ID number is already registered."
                    )
            else:
                if UserProfile.objects.filter(id_number=id_number).exists():
                    raise ValidationError(
                        "This ID number is already registered."
                    )
        
        return id_number

    def clean_phone_number(self):
        """Validate and format phone number"""
        phone = self.cleaned_data.get('phone_number')
        if phone:
            # Remove spaces, dashes, and parentheses
            phone = phone.strip().replace(' ', '').replace('-', '').replace('(', '').replace(')', '')
            
            # Ensure it starts with + or country code
            if not phone.startswith('+'):
                if phone.startswith('0'):
                    phone = '+254' + phone[1:]
                elif phone.startswith('254'):
                    phone = '+' + phone
                elif phone.startswith('7') or phone.startswith('1'):
                    phone = '+254' + phone
                else:
                    raise ValidationError(
                        "Phone number must start with +254, 0, or be a valid format."
                    )
            
            # Validate length (Kenyan numbers: +254 + 9 digits)
            if len(phone) < 12 or len(phone) > 15:
                raise ValidationError(
                    "Invalid phone number length."
                )
        
        return phone

    def clean_date_of_birth(self):
        """Validate date of birth is reasonable"""
        dob = self.cleaned_data.get('date_of_birth')
        if dob:
            today = date.today()
            age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
            
            if age < 5:
                raise ValidationError(
                    "Applicant must be at least 5 years old."
                )
            if age > 100:
                raise ValidationError(
                    "Please verify the date of birth. Age cannot exceed 100 years."
                )
            if dob > today:
                raise ValidationError(
                    "Date of birth cannot be in the future."
                )
        
        return dob


class BursaryApplicationForm(forms.ModelForm):
    """Main bursary application form with custom validation"""
    class Meta:
        model = BursaryApplication
        fields = [
            # list the fields you want on the form, e.g.:
            'first_name', 'last_name', 'email', 'phone',
            'school', 'program', 'amount_requested', 'supporting_document'
        ]
        widgets = {
            'amount_requested': forms.NumberInput(attrs={'min': 0}),
        }
    
    class Meta:
        model = BursaryApplication
        fields = [
            'student_name', 'institution_name', 'admission_number',
            'education_level', 'course_program', 'year_of_study',
            'annual_family_income', 'tuition_fee', 'amount_requested',
            'family_status', 'number_of_siblings', 'siblings_in_school',
            'parent_guardian_name', 'parent_guardian_phone', 'parent_guardian_occupation',
            'reason_for_application', 'previous_bursary_recipient'
        ]
        widgets = {
            'student_name': forms.TextInput(attrs={'placeholder': 'Full Name'}),
            'institution_name': forms.TextInput(attrs={'placeholder': 'School/College/University Name'}),
            'admission_number': forms.TextInput(attrs={'placeholder': 'Student Admission Number'}),
            'course_program': forms.TextInput(attrs={'placeholder': 'e.g., Bachelor of Science'}),
            'annual_family_income': forms.NumberInput(attrs={'placeholder': '0.00', 'step': '0.01', 'min': '0'}),
            'tuition_fee': forms.NumberInput(attrs={'placeholder': '0.00', 'step': '0.01', 'min': '0'}),
            'amount_requested': forms.NumberInput(attrs={'placeholder': '0.00', 'step': '0.01', 'min': '0'}),
            'parent_guardian_phone': forms.TextInput(attrs={'placeholder': '+254712345678'}),
            'number_of_siblings': forms.NumberInput(attrs={'min': '0', 'max': '20'}),
            'siblings_in_school': forms.NumberInput(attrs={'min': '0', 'max': '20'}),
            'year_of_study': forms.NumberInput(attrs={'min': '1', 'max': '8'}),
            'reason_for_application': forms.Textarea(attrs={
                'rows': 5,
                'placeholder': 'Explain why you need this bursary (max 1000 characters)',
                'maxlength': '1000'
            }),
        }

    def clean_student_name(self):
        """Validate student name"""
        name = self.cleaned_data.get('student_name')
        if name:
            # Check minimum length
            if len(name.strip()) < 3:
                raise ValidationError(
                    "Student name must be at least 3 characters long."
                )
            # Check for valid characters (letters, spaces, hyphens, apostrophes)
            import re
            if not re.match(r"^[a-zA-Z\s\-']+$", name):
                raise ValidationError(
                    "Student name must contain only letters, spaces, hyphens, and apostrophes."
                )
        return name.strip()

    def clean_institution_name(self):
        """Validate institution name"""
        name = self.cleaned_data.get('institution_name')
        if name:
            if len(name.strip()) < 3:
                raise ValidationError(
                    "Institution name must be at least 3 characters long."
                )
        return name.strip()

    def clean_admission_number(self):
        """Validate admission number"""
        adm_no = self.cleaned_data.get('admission_number')
        if adm_no:
            adm_no = adm_no.strip().upper()
            if len(adm_no) < 3:
                raise ValidationError(
                    "Admission number must be at least 3 characters long."
                )
        return adm_no

    def clean_annual_family_income(self):
        """Validate family income is within reasonable range"""
        income = self.cleaned_data.get('annual_family_income')
        
        if income is not None:
            if income < 0:
                raise ValidationError("Income cannot be negative.")
            if income > 100000000:  # 100 million
                raise ValidationError(
                    "Income value seems unreasonably high. Please verify."
                )
        return income

    def clean_tuition_fee(self):
        """Validate tuition fee is reasonable"""
        fee = self.cleaned_data.get('tuition_fee')
        
        if fee is not None:
            if fee <= 0:
                raise ValidationError("Tuition fee must be greater than zero.")
            if fee > 10000000:  # 10 million
                raise ValidationError(
                    "Tuition fee seems unreasonably high. Please verify."
                )
        return fee

    def clean_amount_requested(self):
        """Validate that amount requested is reasonable"""
        amount = self.cleaned_data.get('amount_requested')
        
        if amount is not None:
            if amount <= 0:
                raise ValidationError(
                    "Amount requested must be greater than zero."
                )
            if amount > 10000000:  # 10 million
                raise ValidationError(
                    "Amount requested seems unreasonably high. Please verify."
                )
        return amount

    def clean_year_of_study(self):
        """Validate year of study based on education level"""
        year = self.cleaned_data.get('year_of_study')
        level = self.cleaned_data.get('education_level')
        
        if year and level:
            max_years = {
                'primary': 8,
                'secondary': 4,
                'college': 3,
                'university': 6
            }
            
            max_year = max_years.get(level, 8)
            if year > max_year:
                raise ValidationError(
                    f"Year of study cannot exceed {max_year} for {level}."
                )
            if year < 1:
                raise ValidationError(
                    "Year of study must be at least 1."
                )
        return year

    def clean_number_of_siblings(self):
        """Validate number of siblings"""
        siblings = self.cleaned_data.get('number_of_siblings')
        if siblings is not None:
            if siblings < 0:
                raise ValidationError("Number of siblings cannot be negative.")
            if siblings > 20:
                raise ValidationError(
                    "Number of siblings seems unreasonably high. Please verify."
                )
        return siblings

    def clean_siblings_in_school(self):
        """Validate siblings in school (will be cross-checked in clean())"""
        siblings_in_school = self.cleaned_data.get('siblings_in_school')
        if siblings_in_school is not None:
            if siblings_in_school < 0:
                raise ValidationError(
                    "Siblings in school cannot be negative."
                )
        return siblings_in_school

    def clean_parent_guardian_phone(self):
        """Validate and format parent/guardian phone number"""
        phone = self.cleaned_data.get('parent_guardian_phone')
        if phone:
            # Remove spaces, dashes, and parentheses
            phone = phone.strip().replace(' ', '').replace('-', '').replace('(', '').replace(')', '')
            
            # Ensure it starts with + or country code
            if not phone.startswith('+'):
                if phone.startswith('0'):
                    phone = '+254' + phone[1:]
                elif phone.startswith('254'):
                    phone = '+' + phone
                elif phone.startswith('7') or phone.startswith('1'):
                    phone = '+254' + phone
            
            # Validate length
            if len(phone) < 12 or len(phone) > 15:
                raise ValidationError(
                    "Invalid phone number length."
                )
        
        return phone

    def clean_reason_for_application(self):
        """Validate reason for application"""
        reason = self.cleaned_data.get('reason_for_application')
        if reason:
            reason = reason.strip()
            if len(reason) < 50:
                raise ValidationError(
                    "Please provide a more detailed reason (at least 50 characters)."
                )
            if len(reason) > 1000:
                raise ValidationError(
                    "Reason cannot exceed 1000 characters."
                )
        return reason

    def clean(self):
        """
        Cross-field validation
        This method is called after all clean_<fieldname> methods
        """
        cleaned_data = super().clean()
        
        # Validate amount_requested vs tuition_fee
        amount_requested = cleaned_data.get('amount_requested')
        tuition_fee = cleaned_data.get('tuition_fee')
        
        if amount_requested and tuition_fee:
            if amount_requested > tuition_fee:
                raise ValidationError({
                    'amount_requested': "Amount requested cannot exceed the tuition fee."
                })
            
            # Warn if requesting less than 10% of tuition
            if amount_requested < (tuition_fee * 0.1):
                self.add_error('amount_requested', 
                    "Amount requested seems low compared to tuition fee. Please verify."
                )
        
        # Cross-field validation: siblings_in_school vs number_of_siblings
        siblings_in_school = cleaned_data.get('siblings_in_school')
        number_of_siblings = cleaned_data.get('number_of_siblings')
        
        if siblings_in_school is not None and number_of_siblings is not None:
            if siblings_in_school > number_of_siblings:
                raise ValidationError({
                    'siblings_in_school': (
                        f"Siblings in school ({siblings_in_school}) cannot exceed "
                        f"total number of siblings ({number_of_siblings})."
                    )
                })
        
        # Validate year_of_study against education_level (cross-check)
        year_of_study = cleaned_data.get('year_of_study')
        education_level = cleaned_data.get('education_level')
        
        if year_of_study and education_level:
            max_years = {
                'primary': 8,
                'secondary': 4,
                'college': 3,
                'university': 6
            }
            if year_of_study > max_years.get(education_level, 8):
                raise ValidationError({
                    'year_of_study': (
                        f"Year {year_of_study} is not valid for {education_level}. "
                        f"Maximum is {max_years.get(education_level)}."
                    )
                })
        
        # Validate financial logic: high income vs high request
        annual_family_income = cleaned_data.get('annual_family_income')
        if annual_family_income and tuition_fee:
            # If family income is more than 10x tuition fee, question the need
            if annual_family_income > (tuition_fee * 10):
                self.add_error('annual_family_income',
                    "Family income seems sufficient for tuition. Please explain in 'Reason for Application'."
                )
        
        return cleaned_data


class DocumentUploadForm(forms.ModelForm):
    """Form for uploading supporting documents with file validation"""
    
    class Meta:
        model = Document
        fields = ['document_type', 'file', 'description']
        widgets = {
            'description': forms.TextInput(attrs={
                'placeholder': 'Brief description of the document'
            }),
        }

    # Override the file field with validators
    file = forms.FileField(
        validators=[
            FileExtensionValidator(
                allowed_extensions=['pdf', 'jpg', 'jpeg', 'png', 'doc', 'docx'],
                message='Only PDF, JPG, PNG, DOC, and DOCX files are allowed.'
            )
        ],
        help_text='Allowed formats: PDF, JPG, PNG, DOC, DOCX (Max size: 5MB)',
        widget=forms.FileInput(attrs={'accept': '.pdf,.jpg,.jpeg,.png,.doc,.docx'})
    )

    def clean_file(self):
        """Validate file size"""
        file = self.cleaned_data.get('file')
        
        if file:
            # Check file size (max 5MB)
            max_size = 5 * 1024 * 1024  # 5MB in bytes
            if file.size > max_size:
                raise ValidationError(
                    f"File size cannot exceed 5MB. Current size: {file.size / (1024*1024):.2f}MB"
                )
            
            # Additional check: ensure file is not empty
            if file.size == 0:
                raise ValidationError("The uploaded file is empty.")
        
        return file

    def clean_description(self):
        """Validate description if provided"""
        description = self.cleaned_data.get('description')
        if description:
            description = description.strip()
            if len(description) > 200:
                raise ValidationError(
                    "Description cannot exceed 200 characters."
                )
        return description

    def clean(self):
        """Cross-field validation for documents"""
        cleaned_data = super().clean()
        
        document_type = cleaned_data.get('document_type')
        file = cleaned_data.get('file')
        
        # Ensure required documents have files
        required_docs = ['id_copy', 'admission_letter', 'fee_structure']
        if document_type in required_docs and not file:
            raise ValidationError({
                'file': f"{document_type.replace('_', ' ').title()} is required."
            })
        
        return cleaned_data


# Formset for handling multiple document uploads
DocumentFormSet = forms.inlineformset_factory(
    BursaryApplication,
    Document,
    form=DocumentUploadForm,
    extra=3,
    max_num=10,
    can_delete=True,
    validate_max=True,
    min_num=1,  # Require at least one document
    validate_min=True
)