from django.test import TestCase, Client
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth.models import User
from datetime import date

from .models import BursaryApplication, UserProfile, Document
from .forms import MultiStepBursaryApplicationForm, DocumentUploadForm, DocumentFormSet
from .views import bursary_apply # Import the function-based view

# --- Helper Functions and Mock Data ---

def get_minimal_valid_data(user_suffix="100"):
    """
    Generates a dictionary of minimal, valid data required by 
    MultiStepBursaryApplicationForm and related models.
    """
    id_number = f"0000{user_suffix}"
    
    return {
        # STEP 1: Personal Details (Maps to User & UserProfile)
        'fullName': f'Test Applicant {user_suffix}',
        'email': f'test_{user_suffix}@example.com',
        'phone': f'0712345{user_suffix}',
        'idNumber': id_number, # Used as admission_number, profile id, and username key
        'dob': date(1995, 1, 1).strftime('%Y-%m-%d'),
        'county': 'West Pokot',
        'subCounty': 'Pokot Central',
        'ward': 'Kacheliba',
        'village': 'A Village',
        'location': 'A Location',
        'subLocation': 'A Sub-Location',
        
        # STEP 2: Institution Details (Maps to BursaryApplication)
        'institution': 'Test High School',
        'level': 'secondary',
        'course': 'Form 4',
        'yearForm': 4,
        'instCounty': 'Test County',
        'instContact': '0721000000',
        'term1': 'A', 'term2': 'A', 'term3': 'A',
        
        # Financial Details (Required by BursaryApplication model)
        'annual_family_income': 50000.00,
        'tuition_fee': 20000.00,
        'amount_requested': 15000.00,
        
        # STEP 3: Family Details
        'singleParent': 'False',
        'family_status': 'Both Parents Alive',
        'number_of_siblings': 2,
        'siblings_in_school': 1,
        'fatherName': 'Test Father', 'motherName': 'Test Mother',
        'fatherOccupation': 'Farmer', 'motherOccupation': 'Casual Labour',
        'guardianName': 'Test Guardian', 'parentId': '12345678',
        'parentPhone': '0722123456', 'relation': 'Parent',
        'feesProvider': 'parents',
        
        # Additional Info
        'reason_for_application': 'Financial hardship due to drought.',
        'previousBursary': 'False',
        'disability': 'False',
        'orphan': 'False',
        
        # STEP 5: Declaration & Chief Verification
        'signature': 'Test Applicant Signature',
        'studentDate': date.today().strftime('%Y-%m-%d'),
        'parentSignature': 'Test Parent Signature',
        'parentDate': date.today().strftime('%Y-%m-%d'),
        'chiefFullName': 'Chief John Doe',
        'chiefSubLocation': 'A Sub-Location',
        'chiefCounty': 'West Pokot',
        'chiefSubCounty': 'Pokot Central',
        'chiefLocation': 'A Location',
        'chiefComments': 'Verified and recommended.',
        'chiefSignature': 'Chief Signature',
        'chiefDate': date.today().strftime('%Y-%m-%d'),
        
        # Formset management data (for DocumentFormSet)
        'document_formset-TOTAL_FORMS': 1,
        'document_formset-INITIAL_FORMS': 0,
        'document_formset-MIN_NUM_FORMS': 0,
        'document_formset-MAX_NUM_FORMS': 10,
    }

def get_document_files(prefix):
    """Generates mock document file data."""
    # Create a simple mock file
    mock_file = SimpleUploadedFile(
        "test_doc.pdf", b"file_content", content_type="application/pdf"
    )
    
    # Files for the DocumentFormSet (Step 4)
    files = {
        f'{prefix}-0-file': mock_file,
    }
    
    # Mock file for the Chief's rubberStamp (Step 5 - single file upload)
    files['rubberStamp'] = SimpleUploadedFile(
        "rubber_stamp.jpg", b"stamp_content", content_type="image/jpeg"
    )
    
    return files


# --- Test Case Class ---

class BursaryApplyViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.url = reverse('bursary_apply')
        self.success_url = reverse('bursary_success')
        self.valid_data = get_minimal_valid_data()
        self.valid_files = get_document_files('document_formset')

    def test_get_request_renders_form(self):
        """Test that a GET request renders the application form."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'applications/busary_form.html')
        self.assertIsInstance(response.context['form'], MultiStepBursaryApplicationForm)
        self.assertIsInstance(response.context['document_formset'], DocumentFormSet)

    def test_successful_application_submission(self):
        """
        Test a complete, successful form submission creates all required model instances.
        """
        response = self.client.post(self.url, data=self.valid_data, files=self.valid_files, follow=True)
        
        # 1. Check redirection to success page
        self.assertRedirects(response, self.success_url)
        
        # 2. Check model creation counts
        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(UserProfile.objects.count(), 1)
        self.assertEqual(BursaryApplication.objects.count(), 1)
        
        # Documents: 1 from Formset + 1 for 'rubberStamp'
        self.assertEqual(Document.objects.count(), 2) 

        # 3. Check data integrity
        application = BursaryApplication.objects.first()
        profile = UserProfile.objects.first()
        user = User.objects.first()
        
        # Check User and Profile linkage
        self.assertEqual(user.username, self.valid_data['idNumber'])
        self.assertEqual(user.email, self.valid_data['email'])
        self.assertEqual(profile.user, user)
        self.assertEqual(profile.id_number, self.valid_data['idNumber'])
        
        # Check Application linkage and a key field
        self.assertEqual(application.user_profile, profile)
        self.assertEqual(application.institution_name, 'Test High School')
        
        # Check Document creation (specifically the rubber stamp)
        rubber_stamp_doc = Document.objects.filter(description='Chief Verification Rubber Stamp').first()
        self.assertIsNotNone(rubber_stamp_doc)
        self.assertEqual(rubber_stamp_doc.application, application)


    def test_invalid_data_shows_error(self):
        """Test submission with missing required data fails validation."""
        invalid_data = self.valid_data.copy()
        # Remove a required field
        invalid_data.pop('fullName') 
        
        response = self.client.post(self.url, data=invalid_data, files=self.valid_files)
        
        # Should re-render the form page with errors
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Please correct the errors below and try again.')
        
        # Check that no objects were created
        self.assertEqual(BursaryApplication.objects.count(), 0)
        self.assertEqual(User.objects.count(), 0)

    def test_existing_user_profile_is_updated(self):
        """
        Test that if a User/UserProfile exists (based on ID number), 
        a new application links to the existing profile, and the profile is updated.
        """
        # Create initial user data
        initial_data = get_minimal_valid_data(user_suffix="200")
        initial_user = User.objects.create(
            username=initial_data['idNumber'], 
            email='old@email.com', 
            first_name='Old Name'
        )
        initial_profile = UserProfile.objects.create(
            user=initial_user, 
            id_number=initial_data['idNumber'],
            phone_number='0700000000',
            date_of_birth=date(1990, 1, 1),
            county='Old County', sub_county='Old Sub', ward='Old Ward', village='Old Village'
        )
        
        # New submission data using the same ID
        new_data = get_minimal_valid_data(user_suffix="200")
        new_data['email'] = 'new@email.com' # Change email to test update
        
        # Submit the new application
        self.client.post(self.url, data=new_data, files=self.valid_files, follow=True)
        
        # Check that no new User/Profile was created
        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(UserProfile.objects.count(), 1)
        self.assertEqual(BursaryApplication.objects.count(), 1)
        
        # Check that the existing user was updated
        updated_user = User.objects.get(pk=initial_user.pk)
        self.assertEqual(updated_user.email, 'new@email.com')
        
        # Check that the application is linked to the updated profile
        application = BursaryApplication.objects.first()
        self.assertEqual(application.user_profile.pk, initial_profile.pk)