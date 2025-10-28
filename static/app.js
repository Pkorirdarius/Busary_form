document.addEventListener('DOMContentLoaded', function () {
const form = document.getElementById('bursaryForm');
const sections = form.querySelectorAll('.form-section');
const progressFill = document.getElementById('progressFill');
const steps = document.querySelectorAll('.progress-steps .step');
// Conditional fields
const orphanNote = document.getElementById('orphanNote');
const disabilityDetails = document.getElementById('disabilityDetails');
const previousBursaryDetails = document.getElementById('previousBursaryDetails');
const previousBursaryDetailsContinued = document.getElementById('previousBursaryDetailsContinued');
const providerNote = document.getElementById('providerNote');

// NOTE: The conflicting initial inline styles (e.g., orphanNote.style.display = 'none';) 
// have been REMOVED. The field hiding is now handled entirely by the .conditional class in style.css.

// Set defaults
// FIX 1: Change 'No' to 'False' for initial defaults
document.querySelector('input[name="orphan"][value="False"]').checked = true;
document.querySelector('input[name="disability"][value="False"]').checked = true;
document.querySelector('input[name="previousBursary"][value="False"]').checked = true;
document.querySelector('input[name="singleParent"][value="False"]').checked = true;

// Central function to handle all conditional field visibility
function handleConditionalFields() {
  // 1. Get current states (using element checks for 'True' value)
  const isOrphan = document.querySelector('input[name="orphan"][value="True"]:checked');
  const hasDisability = document.querySelector('input[name="disability"][value="True"]:checked');
  const previousBursary = document.querySelector('input[name="previousBursary"][value="True"]:checked');
  const bothParentsAlive = document.querySelector('input[name="bothParentsAlive"][value="True"]:checked');
  const singleParent = document.querySelector('input[name="singleParent"][value="True"]:checked');
  
  // 2. Set visibility for conditional fields
  const showHide = (el, show) => {
    if (el) {
      el.classList.toggle('show', show);
      
      // FIX 1: Implement required attribute management
      el.querySelectorAll('input, select, textarea').forEach(field => {
        // 1. Use a data attribute to store the *original* required state (only on first run)
        if (field.dataset.originalRequired === undefined) {
          field.dataset.originalRequired = field.hasAttribute('required') ? 'true' : 'false';
        }
        
        // 2. Set 'required' only if 'show' is true AND the field was originally required
        if (show && field.dataset.originalRequired === 'true') {
          field.setAttribute('required', 'required');
        } else {
          // Remove required attribute when hidden or if it wasn't originally required
          field.removeAttribute('required');
        }
      });
    }
  };
  
  // 1. Orphan
  showHide(orphanNote, isOrphan);
  // 2. Provider Note: Required if (Orphan=True) OR (BothParentsAlive=False) OR (SingleParent=True)
  const needsProviderNote = isOrphan || !bothParentsAlive || singleParent;
  showHide(providerNote, needsProviderNote);
  // 3. Disability
  showHide(disabilityDetails, hasDisability);
  // 4. Previous Bursary
  showHide(previousBursaryDetails, previousBursary);
  showHide(previousBursaryDetailsContinued, previousBursary);
}

// A. Initial Call: Run once on page load to set the initial state (based on defaults or pre-filled data)
handleConditionalFields();
// B. Event Listener: Run whenever any radio button is changed
// FIX 2: Removed the redundant event listener block that was previously placed above this line.
form.querySelectorAll('input[type="radio"]').forEach(radio => {
  radio.addEventListener('change', handleConditionalFields);
});

// Navigation
// ---------- Navigation ----------
document.getElementById('toStep2').addEventListener('click', () => goToStep(2));
document.getElementById('backTo1').addEventListener('click', () => goToStep(1));
document.getElementById('toStep3').addEventListener('click', () => goToStep(3));
document.getElementById('backTo2').addEventListener('click', () => goToStep(2));
document.getElementById('toStep4').addEventListener('click', () => goToStep(4));
document.getElementById('backTo3').addEventListener('click', () => goToStep(3));
document.getElementById('toStep5').addEventListener('click', () => goToStep(5));
document.getElementById('backTo4').addEventListener('click', () => goToStep(4));


// ---------- UI state ----------
let currentStep = 1;
const totalSteps = sections.length;

// progress elements
function updateProgress() {
  const pct = Math.round((currentStep - 1) / (totalSteps - 1) * 100);
  progressFill.style.width = pct + '%';

  steps.forEach((st, i) => {
    st.classList.toggle('active', i + 1 === currentStep);
  });
  sections.forEach(s => {
    const step = parseInt(s.dataset.step,10);
    s.classList.toggle('active', step === currentStep);
    s.classList.toggle('completed', step < currentStep);
    const sn = s.querySelector('.section-number');
    if (sn) sn.classList.toggle('active', step === currentStep);
  });
}
updateProgress();

  // ---------- Navigation buttons ----------
  function goToStep(n){
    // basic validation before moving forward from certain steps
    if (n > currentStep) {
      if (!validateStep(currentStep)) return;
    }
    currentStep = n;
    updateProgress();
    window.scrollTo({top:0, behavior:'smooth'});
  }

  // ---------- File inputs: preview + base64 extraction ----------
  async function fileToBase64(file){
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = () => resolve(reader.result.split(",")[1]); // return base64 string (no prefix)
      reader.onerror = reject;
      reader.readAsDataURL(file);
    });
  }

  function setupFilePreview(inputId, previewId){
    const input = document.getElementById(inputId);
    const preview = document.getElementById(previewId);
    if (input && preview) {
      input.addEventListener('change', ()=>{
        const f = input.files[0];
        if (!f) { preview.innerText = ''; return; }
        preview.innerText = f.name + ' (' + Math.round(f.size/1024) + ' KB)';
      });
    }
  }
  setupFilePreview('idFile','idFilePreview');
  setupFilePreview('reportForm','reportFormPreview');
  setupFilePreview('parentIdFile','parentIdFilePreview');
  setupFilePreview('studentIdFile','studentIdFilePreview');
  setupFilePreview('instIdFile','instIdFilePreview');
  setupFilePreview('instLetter','instLetterPreview');
  setupFilePreview('guardianFile','guardianFilePreview');
  setupFilePreview('passportPhoto','passportPhotoPreview');

  // ---------- Simple validation ----------
  function validateStep(step){
    // only check required fields in the active step
    const sec = document.querySelector('.form-section[data-step="'+step+'"]');
    const requiredEls = sec.querySelectorAll('[required]');
    for (let el of requiredEls){
      if (el.type === 'file') {
        if (el.files.length === 0) {
          showError("Please attach required file(s) before continuing.");
          el.focus();
          return false;
        }
      } else if (el.tagName === 'SELECT' && el.value === '') {
        showError("Please select required options.");
        el.focus();
        return false;
      } else if (!el.value || el.value.trim() === '') {
        showError("Please fill all required fields in this section.");
        el.focus();
        return false;
      }
    }
    // 2. NEW LOGIC: Validate radio button groups marked as required
    const radioGroups = sec.querySelectorAll('.form-group .radio-group');
    for (let groupDiv of radioGroups) {
      // Check if the closest label is marked as required (based on busary_form.html structure)
      const labelEl = groupDiv.closest('.form-group')?.querySelector('label.required');

      if (labelEl) {
        const groupName = groupDiv.querySelector('input[type="radio"]')?.name;
        // Only check if a group name exists and the group is visible
        if (groupName && groupDiv.offsetParent !== null) {
          const checked = sec.querySelector(`input[name="${groupName}"]:checked`);
          // Clean the label text for the error message
          const groupLabel = labelEl.textContent.replace('*', '').trim();
          
          if (!checked) {
            showError(`Please select an option for: ${groupLabel}.`);
            groupDiv.closest('.form-group').classList.add('has-error');
            // Scroll to the error
            groupDiv.closest('.form-group').scrollIntoView({ behavior: 'smooth', block: 'center' });
            return false;
          } else {
            groupDiv.closest('.form-group').classList.remove('has-error');
          }
        }
      }
    }
    clearMessages();
    return true;
  }
  // Add this validation function after the validateStep function in app.js

function validateFinancialFields() {
  const annualIncome = parseFloat(document.getElementById('annual_family_income')?.value || 0);
  const tuitionFee = parseFloat(document.getElementById('tuition_fee')?.value || 0);
  const amountRequested = parseFloat(document.getElementById('amount_requested')?.value || 0);
  
  // Validate tuition fee is greater than 0
  if (tuitionFee <= 0) {
    showError('Tuition fee must be greater than zero.');
    document.getElementById('tuition_fee').focus();
    return false;
  }
  
  // Validate amount requested doesn't exceed tuition fee
  if (amountRequested > tuitionFee) {
    showError(`Amount requested (KES ${amountRequested.toLocaleString()}) cannot exceed tuition fee (KES ${tuitionFee.toLocaleString()}).`);
    document.getElementById('amount_requested').focus();
    return false;
  }
  
  // Validate amount requested is reasonable (at least 10% of tuition)
  if (amountRequested < tuitionFee * 0.1) {
    if (!confirm(`Amount requested (KES ${amountRequested.toLocaleString()}) is less than 10% of tuition fee. Do you want to continue?`)) {
      document.getElementById('amount_requested').focus();
      return false;
    }
  }
  
  // Check if family income is very high compared to tuition
  if (annualIncome > tuitionFee * 10) {
    if (!confirm(`Your annual family income (KES ${annualIncome.toLocaleString()}) appears sufficient for tuition. Please ensure your reason for application clearly explains your financial need. Continue?`)) {
      document.getElementById('reason_for_application').focus();
      return false;
    }
  }
  
  return true;
}

// Update the toStep3 button click handler to include financial validation
document.getElementById('toStep3').addEventListener('click', () => {
  if (validateStep(2) && validateFinancialFields()) {
    goToStep(3);
  }
});

// Add real-time validation for amount_requested
document.getElementById('amount_requested')?.addEventListener('blur', function() {
  const tuitionFee = parseFloat(document.getElementById('tuition_fee')?.value || 0);
  const amountRequested = parseFloat(this.value || 0);
  
  if (amountRequested > tuitionFee && tuitionFee > 0) {
    showError(`Amount requested cannot exceed tuition fee of KES ${tuitionFee.toLocaleString()}`);
    this.value = '';
    this.focus();
  } else {
    clearMessages();
  }
});

// Update the form submission payload to include new fields
// Add these lines to the payload object in the form submit handler:

// Inside the form submit event listener, update the payload object:
/*
payload.annual_family_income = document.getElementById('annual_family_income').value.trim();
payload.tuition_fee = document.getElementById('tuition_fee').value.trim();
payload.amount_requested = document.getElementById('amount_requested').value.trim();
payload.reason_for_application = document.getElementById('reason_for_application').value.trim();
payload.number_of_siblings = document.getElementById('number_of_siblings')?.value.trim() || '0';
payload.siblings_in_school = document.getElementById('siblings_in_school')?.value.trim() || '0';
*/

  // ---------- Submit handler ----------
  form.addEventListener('submit', (e) => {
    // 1. Final validation across all steps: ensure step 1-5 required fields present
    
    // Check current step first (optional, but good for immediate feedback)
    if (!validateStep(currentStep)) {
        e.preventDefault(); // Prevent native submit if current step fails
        return;
    }
    
    // Check all steps before final submission
    for (let s = 1; s <= totalSteps; s++) {
        if (!validateStep(s)) {
            // If validation fails on any step, stop the native submission
            e.preventDefault(); 
            
            // Navigate the user back to the first step with an error
            goToStep(s);
            
            showError('Please correct the highlighted errors before submitting.');
            
            // Re-enable button after showing error
            document.getElementById('submitBtn').disabled = false;
            return;
        }
    }
    
    // 2. Allow Native Submission if All Validation Passes
    
    // Disable the button to prevent double-submission
    document.getElementById('submitBtn').disabled = true;
    
    // FIX 3 (Option 2): Removed the client-side progress message to rely on server response.
    
    // DO NOT CALL e.preventDefault() HERE. The form will submit naturally.
  });

  // ---------- Messages ----------
  const successMsg = document.getElementById('successMsg');
  const errorMsg = document.getElementById('errorMsg');
  function showSuccess(text) { successMsg.innerText = text; successMsg.style.display='block'; errorMsg.style.display='none'; }
  function showError(text) { errorMsg.innerText = text; errorMsg.style.display='block'; successMsg.style.display='none'; }
  function clearMessages() { errorMsg.style.display='none'; successMsg.style.display='none'; }
  // showProgressMessage function removed as requested.

  // help button
  document.getElementById('helpBtn').addEventListener('click', ()=> {
    alert('Need help? Contact the County Bursary Office or use the email/phone provided in the application instructions.');
  });

  // quick keyboard navigation: allow Enter to advance within required fields
  document.addEventListener('keydown', (e)=> {
    if (e.key === 'Enter' && currentStep < totalSteps) {
      e.preventDefault();
      goToStep(currentStep + 1);
    }
  });
});