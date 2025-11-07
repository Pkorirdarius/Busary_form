from django import forms
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
from django.core.cache import cache
from .models import UserProfile, BursaryApplication, Document
from django.contrib.auth.models import User
from datetime import date
import re


class UserProfileForm(forms.ModelForm):
    """Form for user profile information with enhanced error messages"""
    first_name = forms.CharField(
        max_length=150, 
        required=True,
        error_messages={
            'required': 'Please enter your first name.',
            'max_length': 'First name cannot exceed 150 characters.'
        }
    )
    last_name = forms.CharField(
        max_length=150, 
        required=True,
        error_messages={
            'required': 'Please enter your last name.',
            'max_length': 'Last name cannot exceed 150 characters.'
        }
    )
    email = forms.EmailField(
        required=True,
        error_messages={
            'required': 'Please provide a valid email address.',
            'invalid': 'Please enter a valid email format (e.g., name@example.com).'
        }
    )
    class Meta:
        model = UserProfile
        fields = ['phone_number', 'id_number', 'date_of_birth', 'county', 
                  'sub_county', 'ward', 'village', 'location', 'sub_location']
        widgets = {
            'date_of_birth': forms.DateInput(attrs={
                'type': 'date',
                'max': date.today().isoformat()
            }),
            'phone_number': forms.TextInput(attrs={
                'placeholder': '+254712345678',
                'pattern': r'^\+?254[17]\d{8}$',
                'title': 'Enter a valid Kenyan phone number starting with +254 or 0'
            }),
            'id_number': forms.TextInput(attrs={
                'placeholder': 'National ID Number',
                'pattern': r'\d{7,9}',
                'title': 'Enter your 7-9 digit ID number'
            }),
        }
        error_messages = {
            'phone_number': {
                'required': 'Phone number is required for contact purposes.',
                'invalid': 'Please enter a valid phone number format.'
            },
            'id_number': {
                'required': 'National ID/Birth Certificate number is required.',
                'unique': 'This ID number is already registered in our system.'
            },
            'date_of_birth': {
                'required': 'Date of birth is required.',
                'invalid': 'Please enter a valid date.'
            }
        }
    def clean_email(self):
        """Validate email is not already in use - optimized with caching"""
        email = self.cleaned_data.get('email')
        if not email:
            return email
            
        cache_key = f'email_exists_{email}'
        exists = cache.get(cache_key)
        
        if exists is None:
            if hasattr(self, 'instance') and self.instance.pk:
                exists = User.objects.filter(email=email).exclude(
                    pk=self.instance.user.pk
                ).exists()
            else:
                exists = User.objects.filter(email=email).exists()
            cache.set(cache_key, exists, 300)  # Cache for 5 minutes
        
        if exists:
            raise ValidationError(
                "This email address is already registered. Please use a different email or contact support if this is your email.",
                code='duplicate_email'
            )
        return email

    def clean_id_number(self):
        """Validate ID number format and uniqueness - optimized"""
        id_number = self.cleaned_data.get('id_number')
        if not id_number:
            return id_number
            
        # Remove spaces and convert to string
        id_number = str(id_number).strip().replace(' ', '')
        
        # Validate format
        if len(id_number) < 7 or len(id_number) > 9:
            raise ValidationError("ID number must be between 7 and 9 digits. You entered: %(length)d digits.", params={'length': len(id_number)},code='invalid_length')
        
        if not id_number.isdigit():
            raise ValidationError("ID number must contain only digits(0-9).",code='invalid_format')
        
        # Check uniqueness with caching
        cache_key = f'id_exists_{id_number}'
        exists = cache.get(cache_key)
        
        if exists is None:
            if hasattr(self, 'instance') and self.instance.pk:
                exists = UserProfile.objects.filter(id_number=id_number).exclude(
                    pk=self.instance.pk
                ).exists()
            else:
                exists = UserProfile.objects.filter(id_number=id_number).exists()
            cache.set(cache_key, exists, 300)
        
        if exists:
            raise ValidationError("This ID number is already registered.")
        
        return id_number

    def clean_phone_number(self):
        """Validate and format phone number"""
        phone = self.cleaned_data.get('phone_number')
        if not phone:
            return phone
            
        # Remove spaces, dashes, and parentheses
        phone = phone.strip().replace(' ', '').replace('-', '').replace('(', '').replace(')', '')
        
        # Format Kenyan numbers
        if not phone.startswith('+'):
            if phone.startswith('0'):
                phone = '+254' + phone[1:]
            elif phone.startswith('254'):
                phone = '+' + phone
            elif phone.startswith('7') or phone.startswith('1'):
                phone = '+254' + phone
            else:
                raise ValidationError("Phone number must start with +254, 0, or be a valid format.")
        
        # Validate length
        if len(phone) < 12 or len(phone) > 13:
            raise ValidationError("Invalid phone number length.number must be 10 digits long.",code='invalid_length')
        # Validate Kenyan mobile prefixes (Safaricom, Airtel, Telkom)
        if not re.match(r'^\+254[17]\d{8}$', phone):
            raise ValidationError(
                "Please enter a valid Kenyan mobile number (Safaricom, Airtel, or Telkom).",
                code='invalid_prefix'
            )
        return phone

    def clean_date_of_birth(self):
        """Validate date of birth is reasonable"""
        dob = self.cleaned_data.get('dob')
        if not dob:
            return dob
            
        today = date.today()
        age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
        
        if age < 5:
            raise ValidationError("Applicant must be at least 5 years old.")
        if age > 100:
            raise ValidationError("Please verify the date of birth. Age cannot exceed 100 years.")
        if dob > today:
            raise ValidationError("Date of birth cannot be in the future.")
        
        return dob


class BaseBursaryApplicationForm(forms.ModelForm):
    """Base form for bursary application model fields"""
    class Meta:
        model = BursaryApplication
        fields = [
            'student_name', 'institution_name', 'admission_number',
            'education_level', 'course_program', 'year_of_study',
            'annual_family_income', 'tuition_fee', 'amount_requested',
            'family_status', 'number_of_siblings', 'siblings_in_school',
            'parent_guardian_name', 'parent_guardian_phone', 'parent_guardian_occupation',
            'reason_for_application', 'previous_bursary_recipient',
            'inst_county', 'inst_contact', 'term1_score', 'term2_score', 'term3_score',
            'father_name', 'mother_name', 'guardian_relation', 'father_occupation',
            'mother_occupation', 'parent_id_number', 'is_single_parent',
            'fees_provider', 'other_fees_provider', 'cdf_amount', 'ministry_amount', 
            'county_gov_amount', 'other_bursary_amount', 'has_disability', 
            'disability_nature', 'disability_reg_no', 'is_orphan',
            'student_signature_name', 'student_declaration_date',
            'parent_signature_name', 'parent_declaration_date',
            'chief_full_name', 'chief_sub_location', 'chief_county',
            'chief_sub_county', 'chief_location', 'chief_comments',
            'chief_signature_name', 'chief_date'
        ]
        widgets = {
            'annual_family_income': forms.NumberInput(attrs={'placeholder': '0.00', 'step': '0.01', 'min': '0'}),
            'tuition_fee': forms.NumberInput(attrs={'placeholder': '0.00', 'step': '0.01', 'min': '0'}),
            'amount_requested': forms.NumberInput(attrs={'placeholder': '0.00', 'step': '0.01', 'min': '0'}),
            'reason_for_application': forms.Textarea(attrs={
                'rows': 5,
                'placeholder': 'Explain why you need this bursary (max 1000 characters)',
                'maxlength': '1000'
            }),
        }

    # Compiled regex patterns for better performance
    NAME_PATTERN = re.compile(r"^[a-zA-Z\s\-']+$")

    def clean_student_name(self):
        """Validate student name"""
        name = self.cleaned_data.get('student_name')
        if name:
            name = name.strip()
            if len(name) < 3:
                raise ValidationError("Student name must be at least 3 characters long.")
            if not self.NAME_PATTERN.match(name):
                raise ValidationError("Student name must contain only letters, spaces, hyphens, and apostrophes.")
        return name

    def clean(self):
        """Cross-field validation"""
        cleaned_data = super().clean()
        
        # Validate amount_requested vs tuition_fee
        amount_requested = cleaned_data.get('amount_requested')
        tuition_fee = cleaned_data.get('tuition_fee')
        
        if amount_requested and tuition_fee:
            if amount_requested > tuition_fee:
                raise ValidationError({
                    'amount_requested': "Amount requested cannot exceed the tuition fee."
                })
        
        # Validate siblings logic
        siblings_in_school = cleaned_data.get('siblings_in_school')
        number_of_siblings = cleaned_data.get('number_of_siblings')
        
        if siblings_in_school is not None and number_of_siblings is not None:
            if siblings_in_school > number_of_siblings:
                raise ValidationError({
                    'siblings_in_school': f"Siblings in school ({siblings_in_school}) cannot exceed total siblings ({number_of_siblings})."
                })
        
        # Validate family status consistency
        is_orphan = cleaned_data.get('is_orphan')
        is_single_parent = cleaned_data.get('is_single_parent')
        family_status = cleaned_data.get('family_status')
        
        if is_orphan and family_status != 'orphan':
            cleaned_data['family_status'] = 'orphan'
        elif is_single_parent and family_status != 'single_parent':
            cleaned_data['family_status'] = 'single_parent'
        
        return cleaned_data


class MultiStepBursaryApplicationForm(forms.Form):
    """Multi-step form combining all application data"""
    
    # STEP 1: Personal Details
    fullName = forms.CharField(max_length=200, label="Student's Full Name")
    idNumber = forms.CharField(max_length=20, label="ID/Birth Cert Number")
    dob = forms.DateField(label="Date of Birth", widget=forms.DateInput(attrs={'type': 'date'}))
    gender = forms.ChoiceField(choices=[('male', 'Male'), ('female', 'Female'), ('other', 'Other')], label="Gender")
    phone = forms.CharField(max_length=15, label="Student Mobile No.")
    email = forms.EmailField(required=False, label="Student Email")
    county = forms.CharField(max_length=100, label="County")
    subCounty = forms.CharField(max_length=100, label="Sub-County")
    ward = forms.CharField(max_length=100, label="Ward")
    location = forms.CharField(max_length=100, label="Location")
    subLocation = forms.CharField(max_length=100, label="Sub-Location")
    village = forms.CharField(max_length=100, label="Village/Estate")
    chiefName = forms.CharField(max_length=200, label="Name of Area Chief/Asst Chief")
    orphan = forms.ChoiceField(choices=[(True, 'Yes'), (False, 'No')], widget=forms.RadioSelect, label="Are you an Orphan?")
    disability = forms.ChoiceField(choices=[(True, 'Yes'), (False, 'No')], widget=forms.RadioSelect, label="Do you have any physical disability?")
    disabilityNature = forms.CharField(max_length=255, required=False, label="Nature of Disability")
    disabilityRegNo = forms.CharField(max_length=50, required=False, label="Disability Registration No.")
    previousBursary = forms.ChoiceField(choices=[(True, 'Yes'), (False, 'No')], widget=forms.RadioSelect, label="Have you received any previous bursary?")
    cdfAmount = forms.DecimalField(max_digits=10, decimal_places=2, min_value=0, required=False, label="CDF Amount")
    ministryAmount = forms.DecimalField(max_digits=10, decimal_places=2, min_value=0, required=False, label="Ministry Amount")
    countyGovAmount = forms.DecimalField(max_digits=10, decimal_places=2, min_value=0, required=False, label="County Gov Amount")
    otherBursary = forms.DecimalField(max_digits=10, decimal_places=2, min_value=0, required=False, label="Other Bursary Amount")
    
    # STEP 2: Institution
    institution = forms.CharField(max_length=200, label="Institution Name")
    level = forms.ChoiceField(choices=BursaryApplication.EDUCATION_LEVEL_CHOICES, label="Education Level")
    course = forms.CharField(max_length=200, label="Course/Program")
    yearForm = forms.IntegerField(min_value=1, max_value=8, label="Year/Form of Study")
    instCounty = forms.CharField(max_length=100, label="Institution County")
    instContact = forms.CharField(max_length=15, label="Institution Contact No.")
    term1 = forms.CharField(max_length=50, required=False, label="Term 1 Score/Grade")
    term2 = forms.CharField(max_length=50, required=False, label="Term 2 Score/Grade")
    term3 = forms.CharField(max_length=50, required=False, label="Term 3 Score/Grade")
    annual_family_income = forms.DecimalField(max_digits=12, decimal_places=2, min_value=0, label="Annual Family Income (KES)")
    tuition_fee = forms.DecimalField(max_digits=10, decimal_places=2, min_value=0.01, label="Total Tuition Fee (KES)")
    amount_requested = forms.DecimalField(max_digits=10, decimal_places=2, min_value=0.01, label="Amount Requested (KES)")
    
    # STEP 3: Family
    fatherName = forms.CharField(max_length=200, required=False, label="Father's Full Name")
    motherName = forms.CharField(max_length=200, required=False, label="Mother's Full Name")
    guardianName = forms.CharField(max_length=200, label="Guardian's Full Name")
    relation = forms.CharField(max_length=100, label="Relation to Guardian")
    fatherOccupation = forms.CharField(max_length=100, required=False, label="Father's Occupation")
    motherOccupation = forms.CharField(max_length=100, required=False, label="Mother's Occupation")
    parentPhone = forms.CharField(max_length=15, label="Parent/Guardian Mobile No.")
    parentId = forms.CharField(max_length=20, required=False, label="Parent/Guardian ID No.")
    bothParentsAlive = forms.ChoiceField(choices=[('True', 'Yes'), ('False', 'No')],required=False,widget=forms.RadioSelect)
    singleParent = forms.ChoiceField(choices=[('True', 'Yes'), ('False', 'No')],required=False, widget=forms.RadioSelect)
    feesProvider = forms.CharField(max_length=100, required=False, label="Who is paying for your fees?")
    otherProvider = forms.CharField(max_length=100, required=False, label="Other Provider (if applicable)")
    reason_for_application = forms.CharField(max_length=1000, widget=forms.Textarea(attrs={'rows': 5}), label="Reason for Application")
    number_of_siblings = forms.IntegerField(min_value=0, max_value=20, required=False, label="Number of Siblings")
    siblings_in_school = forms.IntegerField(min_value=0, max_value=20, required=False, label="Siblings In School")
    
    # STEP 4: Documents (handled by formset)
    idFile = forms.FileField(required=True, label="Student's ID/Birth Certificate")
    reportForm = forms.FileField(required=True, label="Students' Transcript/Report Form")
    parentIdFile = forms.FileField(required=False, label="Parent/Guardian National Identity Card")
    studentIdFile = forms.FileField(required=False, label="Student National Identity Card")
    instIdFile = forms.FileField(required=False, label="Secondary/College/University ID Card")
    instLetter = forms.FileField(required=False, label="Admission Letter")
    guardianFile = forms.FileField(required=False, label="Guardianship Documents")
    passportPhoto = forms.FileField(required=False, label="Student Passport Photo")
    
    # STEP 5: Declaration
    signature = forms.CharField(max_length=200, label="Student Signature (Full Name)")
    studentDate = forms.DateField(label="Date", widget=forms.DateInput(attrs={'type': 'date'}))
    parentSignature = forms.CharField(max_length=200, label="Parent/Guardian Signature (Full Name)")
    parentDate = forms.DateField(label="Date", widget=forms.DateInput(attrs={'type': 'date'}))
    chiefFullName = forms.CharField(max_length=200, required=False, label="Chief/Asst Chief Full Name")
    chiefSubLocation = forms.CharField(max_length=100, required=False, label="Chief's Sub-Location")
    chiefCounty = forms.CharField(max_length=100, required=False, label="Chief's County")
    chiefSubCounty = forms.CharField(max_length=100, required=False, label="Chief's Sub-County")
    chiefLocation = forms.CharField(max_length=100, required=False, label="Chief's Location")
    chiefComments = forms.CharField(max_length=500, required=False, widget=forms.Textarea(attrs={'rows': 3}), label="Chief's Comments")
    chiefSignature = forms.CharField(max_length=200, required=False, label="Chief's Signature (Full Name)")
    chiefDate = forms.DateField(required=False, label="Date", widget=forms.DateInput(attrs={'type': 'date'}))
    rubberStamp = forms.FileField(required=False, label="Official Rubber Stamp")
    notes = forms.CharField(required=False, widget=forms.Textarea(attrs={'rows': 3}), label="Official Use Only Notes")
    
    def clean(self):
        """Cross-field and logic validation"""
        cleaned_data = super().clean()
        
        # Determine family_status
        orphan = cleaned_data.get('orphan') == 'True'
        both_parents_alive = cleaned_data.get('bothParentsAlive') == 'True'
        single_parent = cleaned_data.get('singleParent') == 'True'
        
        if orphan:
            cleaned_data['family_status'] = 'orphan'
            cleaned_data['is_orphan'] = True
        elif single_parent:
            cleaned_data['family_status'] = 'single_parent'
            cleaned_data['is_single_parent'] = True
        elif both_parents_alive:
            cleaned_data['family_status'] = 'both_parents'
            cleaned_data['is_single_parent'] = False
        else:
            cleaned_data['family_status'] = 'guardian'
        
        # Validate financial consistency
        amount_requested = cleaned_data.get('amount_requested')
        tuition_fee = cleaned_data.get('tuition_fee')
        
        if amount_requested and tuition_fee and amount_requested > tuition_fee:
            self.add_error('amount_requested', "Amount requested cannot exceed tuition fee.")
        
        # Validate sibling logic
        siblings_in_school = cleaned_data.get('siblings_in_school', 0)
        number_of_siblings = cleaned_data.get('number_of_siblings', 0)
        # Set defaults if None
        if siblings_in_school is None:
            cleaned_data['siblings_in_school'] = 0
            siblings_in_school = 0
        
        if number_of_siblings is None:
            cleaned_data['number_of_siblings'] = 0
            number_of_siblings = 0
        
        if siblings_in_school > number_of_siblings:
            self.add_error('siblings_in_school', f"Siblings in school cannot exceed total siblings.")
        
        return cleaned_data


class DocumentUploadForm(forms.ModelForm):
    """Form for uploading supporting documents with file validation"""
    
    class Meta:
        model = Document
        fields = ['document_type', 'file', 'description']
        widgets = {
            'description': forms.TextInput(attrs={'placeholder': 'Brief description of the document'}),
        }
        error_messages = {
            'document_type': {
                'required': 'Please select the document type.'
            },
            'file': {
                'required': 'Please upload a file.'
            }
        }

    file = forms.FileField(
        validators=[
            FileExtensionValidator(
                allowed_extensions=['pdf', 'jpg', 'jpeg', 'png', 'doc', 'docx'],
                message='Only PDF, JPG, PNG, DOC, and DOCX files are allowed.'
            )
        ],
        help_text='Allowed formats: PDF, JPG, PNG, DOC, DOCX (Max size: 5MB)',
        widget=forms.FileInput(attrs={'accept': '.pdf,.jpg,.jpeg,.png,.doc,.docx'}),
        error_messages={
            'required': 'Please select a file to upload.',
            'invalid': 'The uploaded file is invalid.'
        }
    )

    def clean_file(self):
        """Validate file size"""
        file = self.cleaned_data.get('file')
        
        if file:
            # Check file size (max 5MB)
            max_size = 5 * 1024 * 1024
            if file.size > max_size:
                raise ValidationError(f"File size cannot exceed 5MB. Current size: {file.size / (1024*1024):.2f}MB")
            
            if file.size == 0:
                raise ValidationError("The uploaded file is empty.")
        
        return file


# Formset for handling multiple document uploads
DocumentFormSet = forms.inlineformset_factory(
    BursaryApplication,
    Document,
    form=DocumentUploadForm,
    extra=3,
    max_num=10,
    can_delete=True,
    validate_max=True,
    min_num=0,
    validate_min=False,
    error_messages={
        'too_many_forms': 'You can upload a maximum of 10 documents.',
        'too_few_forms': 'Please upload at least the required documents.'
    }
)