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


class BaseBursaryApplicationForm(forms.ModelForm):
# ... (BursaryApplicationForm renamed and fields simplified)
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
            
            # NEW fields added to model
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
            'inst_contact': forms.TextInput(attrs={'placeholder': 'Institution Phone/Email'}),
            'parent_id_number': forms.TextInput(attrs={'placeholder': 'Parent/Guardian ID Number'}),
            'student_declaration_date': forms.DateInput(attrs={'type': 'date'}),
            'parent_declaration_date': forms.DateInput(attrs={'type': 'date'}),
            'chief_date': forms.DateInput(attrs={'type': 'date'}),
            'is_single_parent': forms.RadioSelect(choices=[(True, 'Yes'), (False, 'No')]),
            'is_orphan': forms.RadioSelect(choices=[(True, 'Yes'), (False, 'No')]),
            'has_disability': forms.RadioSelect(choices=[(True, 'Yes'), (False, 'No')]),
            'previous_bursary_recipient': forms.RadioSelect(choices=[(True, 'Yes'), (False, 'No')]),
            'chief_comments': forms.Textarea(attrs={'rows': 3}),
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

class MultiStepBursaryApplicationForm(forms.Form):
    """
    A non-ModelForm to handle all fields presented in busary_form.html,
    combining UserProfile, BursaryApplication, and temporary fields.
    The view will handle saving to the respective models.
    """
    
    # STEP 1: PERSONAL DETAILS (Includes UserProfile and BursaryApplication fields)
    fullName = forms.CharField(max_length=200, label="Student's Full Name") # Maps to student_name
    idNumber = forms.CharField(max_length=20, label="ID/Birth Cert Number") # Maps to UserProfile.id_number
    dob = forms.DateField(label="Date of Birth", widget=forms.DateInput(attrs={'type': 'date'})) # Maps to UserProfile.date_of_birth
    gender = forms.ChoiceField(choices=[('male', 'Male'), ('female', 'Female'), ('other', 'Other')], label="Gender") # Will need to be stored in UserProfile or custom field
    phone = forms.CharField(max_length=15, label="Student Mobile No.") # Maps to UserProfile.phone_number
    email = forms.EmailField(required=False, label="Student Email") # Maps to User.email (via UserProfile)

    # Location (Maps to UserProfile fields)
    county = forms.CharField(max_length=100, label="County") # Maps to UserProfile.county
    subCounty = forms.CharField(max_length=100, label="Sub-County") # Maps to UserProfile.sub_county
    ward = forms.CharField(max_length=100, label="Ward") # Maps to UserProfile.ward
    location = forms.CharField(max_length=100, label="Location") # Maps to UserProfile.location (NEW)
    subLocation = forms.CharField(max_length=100, label="Sub-Location") # Maps to UserProfile.sub_location (NEW)
    village = forms.CharField(max_length=100, label="Village/Estate") # Maps to UserProfile.village
    chiefName = forms.CharField(max_length=200, label="Name of Area Chief/Asst Chief") # Temporary form field

    # Status & Disability (Maps to BursaryApplication fields)
    orphan = forms.ChoiceField(choices=[(True, 'Yes'), (False, 'No')], widget=forms.RadioSelect, label="Are you an Orphan?") # Maps to is_orphan
    disability = forms.ChoiceField(choices=[(True, 'Yes'), (False, 'No')], widget=forms.RadioSelect, label="Do you have any physical disability?") # Maps to has_disability
    disabilityNature = forms.CharField(max_length=255, required=False, label="Nature of Disability") # Maps to disability_nature
    disabilityRegNo = forms.CharField(max_length=50, required=False, label="Disability Registration No.") # Maps to disability_reg_no
    
    # Previous Bursary (Maps to BursaryApplication fields)
    previousBursary = forms.ChoiceField(choices=[(True, 'Yes'), (False, 'No')], widget=forms.RadioSelect, label="Have you received any previous bursary?") # Maps to previous_bursary_recipient
    cdfAmount = forms.DecimalField(max_digits=10, decimal_places=2, min_value=0, required=False, label="CDF Amount") # Maps to cdf_amount
    ministryAmount = forms.DecimalField(max_digits=10, decimal_places=2, min_value=0, required=False, label="Ministry Amount") # Maps to ministry_amount
    countyGovAmount = forms.DecimalField(max_digits=10, decimal_places=2, min_value=0, required=False, label="County Gov Amount") # Maps to county_gov_amount
    otherBursary = forms.DecimalField(max_digits=10, decimal_places=2, min_value=0, required=False, label="Other Bursary Amount") # Maps to other_bursary_amount
    
    # STEP 2: INSTITUTION
    institution = forms.CharField(max_length=200, label="Institution Name") # Maps to institution_name
    level = forms.ChoiceField(choices=BursaryApplication.EDUCATION_LEVEL_CHOICES, label="Education Level") # Maps to education_level
    course = forms.CharField(max_length=200, label="Course/Program") # Maps to course_program
    yearForm = forms.IntegerField(min_value=1, max_value=8, label="Year/Form of Study") # Maps to year_of_study
    instCounty = forms.CharField(max_length=100, label="Institution County") # Maps to inst_county (NEW)
    instContact = forms.CharField(max_length=15, label="Institution Contact No.") # Maps to inst_contact (NEW)
    
    # School Performance (Maps to BursaryApplication fields)
    term1 = forms.CharField(max_length=50, required=False, label="Term 1 Score/Grade") # Maps to term1_score
    term2 = forms.CharField(max_length=50, required=False, label="Term 2 Score/Grade") # Maps to term2_score
    term3 = forms.CharField(max_length=50, required=False, label="Term 3 Score/Grade") # Maps to term3_score
    
    annual_family_income = forms.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        min_value=0,
        label="Annual Family Income (KES)",
        help_text="Enter the total annual income of your family"
    )
    tuition_fee = forms.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        min_value=0.01,
        label="Total Tuition Fee (KES)",
        help_text="Enter the full tuition fee for the academic year"
    )
    amount_requested = forms.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        min_value=0.01,
        label="Amount Requested (KES)",
        help_text="Enter the bursary amount you are requesting"
    )
    # STEP 3: FAMILY
    fatherName = forms.CharField(max_length=200, required=False, label="Father's Full Name") # Maps to father_name (NEW)
    motherName = forms.CharField(max_length=200, required=False, label="Mother's Full Name") # Maps to mother_name (NEW)
    guardianName = forms.CharField(max_length=200, label="Guardian's Full Name") # Maps to parent_guardian_name
    relation = forms.CharField(max_length=100, label="Relation to Guardian") # Maps to guardian_relation (NEW)
    fatherOccupation = forms.CharField(max_length=100, required=False, label="Father's Occupation") # Maps to father_occupation (NEW)
    motherOccupation = forms.CharField(max_length=100, required=False, label="Mother's Occupation") # Maps to mother_occupation (NEW)
    parentPhone = forms.CharField(max_length=15, label="Parent/Guardian Mobile No.") # Maps to parent_guardian_phone
    parentId = forms.CharField(max_length=20, required=False, label="Parent/Guardian ID No.") # Maps to parent_id_number (NEW)
    
    # Family Status
    bothParentsAlive = forms.ChoiceField(choices=[(True, 'Yes'), (False, 'No')], widget=forms.RadioSelect, label="Are both parents alive?") # Temporary form field (helps determine family_status)
    singleParent = forms.ChoiceField(choices=[(True, 'Yes'), (False, 'No')], widget=forms.RadioSelect, label="Are you from a single parent family?") # Maps to is_single_parent
    feesProvider = forms.CharField(max_length=100, required=False, label="Who is paying for your fees?") # Maps to fees_provider (NEW)
    otherProvider = forms.CharField(max_length=100, required=False, label="Other Provider (if applicable)") # Maps to other_fees_provider (NEW)
    
    # Missing from form but essential for model: family_status (calculated in clean)
    # Missing from form but essential for model: reason_for_application (The form doesn't show this, but the model requires it - assuming it's hidden or missed)
    # Assuming reason_for_application is collected elsewhere or added:
    reason_for_application = forms.CharField(
        max_length=1000, 
        widget=forms.Textarea(attrs={'rows': 5}), 
        label="Reason for Application"
    ) # Maps to reason_for_application

    # Missing from form but essential for model: number_of_siblings, siblings_in_school (assuming these are missing from the HTML snippet)
    number_of_siblings = forms.IntegerField(min_value=0, max_value=20, required=False, label="Number of Siblings")
    siblings_in_school = forms.IntegerField(min_value=0, max_value=20, required=False, label="Siblings In School")

    # STEP 4: DOCUMENTS (File fields map to the Document model via a FormSet, not the main form)
    # These fields are required for the front-end validation but the actual file data
    # will be handled by DocumentFormSet in the view.
    idFile = forms.FileField(required=True, label="Student's ID/Birth Certificate")
    reportForm = forms.FileField(required=True, label="Students' Transcript/Report Form")
    parentIdFile = forms.FileField(required=False, label="Parent/Guardian National Identity Card")
    studentIdFile = forms.FileField(required=False, label="Student National Identity Card (if applicable)")
    instIdFile = forms.FileField(required=False, label="Secondary/College/University ID Card")
    instLetter = forms.FileField(required=False, label="Admission Letter (Colleges and Universities)")
    guardianFile = forms.FileField(required=False, label="Guardianship Documents (for orphans)")
    passportPhoto = forms.FileField(required=False, label="Student Passport Photo")

    # STEP 5: DECLARATION & SUBMIT
    signature = forms.CharField(max_length=200, label="Student Signature (Full Name)") # Maps to student_signature_name
    studentDate = forms.DateField(label="Date", widget=forms.DateInput(attrs={'type': 'date'})) # Maps to student_declaration_date
    parentSignature = forms.CharField(max_length=200, label="Parent/Guardian Signature (Full Name)") # Maps to parent_signature_name
    parentDate = forms.DateField(label="Date", widget=forms.DateInput(attrs={'type': 'date'})) # Maps to parent_declaration_date
    
    # Verification by Chief
    chiefFullName = forms.CharField(max_length=200, required=False, label="Chief/Asst Chief Full Name") # Maps to chief_full_name
    chiefSubLocation = forms.CharField(max_length=100, required=False, label="Chief's Sub-Location") # Maps to chief_sub_location
    chiefCounty = forms.CharField(max_length=100, required=False, label="Chief's County") # Maps to chief_county
    chiefSubCounty = forms.CharField(max_length=100, required=False, label="Chief's Sub-County") # Maps to chief_sub_county
    chiefLocation = forms.CharField(max_length=100, required=False, label="Chief's Location") # Maps to chief_location
    chiefComments = forms.CharField(max_length=500, required=False, widget=forms.Textarea(attrs={'rows': 3}), label="Chief's Comments") # Maps to chief_comments
    chiefSignature = forms.CharField(max_length=200, required=False, label="Chief's Signature (Full Name)") # Maps to chief_signature_name
    chiefDate = forms.DateField(required=False, label="Date", widget=forms.DateInput(attrs={'type': 'date'})) # Maps to chief_date
    rubberStamp = forms.FileField(required=False, label="Official Rubber Stamp") # New Document field

    notes = forms.CharField(required=False, widget=forms.Textarea(attrs={'rows': 3}), label="Official Use Only Notes") # Temporary form field
    
    def clean(self):
        """Cross-field and logic validation for the combined form."""
        cleaned_data = super().clean()
        
        # 1. Determine family_status based on form inputs
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
        elif cleaned_data.get('relation') and cleaned_data.get('relation').lower() not in ['father', 'mother']:
             cleaned_data['family_status'] = 'guardian' # Fallback if relation is not a parent
        else:
            # Default or error if logic is unclear
            if not cleaned_data.get('family_status'):
                self.add_error(None, "Family status could not be determined. Please check orphan, single parent, and parent status.")

        # 2. Validate fees provider logic
        fees_provider = cleaned_data.get('feesProvider')
        other_provider = cleaned_data.get('otherProvider')
        if fees_provider and fees_provider.lower() == 'other' and not other_provider:
             self.add_error('otherProvider', "If 'Other' is selected as fees provider, please specify the name.")

        # 3. Validate Student Name and ID fields
        # ... (similar validations from BaseBursaryApplicationForm clean methods should be copied/adapted here)
        
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