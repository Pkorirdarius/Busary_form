// Optimized bursary form with proper section hiding/showing
document.addEventListener('DOMContentLoaded', function () {
  // === CACHE ALL DOM ELEMENTS AT STARTUP ===
  const form = document.getElementById('bursaryForm');
  const sections = form.querySelectorAll('.form-section');
  const progressFill = document.getElementById('progressFill');
  const steps = document.querySelectorAll('.progress-steps .step');
  const successMsg = document.getElementById('successMsg');
  const errorMsg = document.getElementById('errorMsg');
  const submitBtn = document.getElementById('submitBtn');
  const helpBtn = document.getElementById('helpBtn');
  
  // Cache conditional field containers
  const conditionalFields = {
    orphanNote: document.getElementById('orphanNote'),
    disabilityDetails: document.getElementById('disabilityDetails'),
    previousBursaryDetails: document.getElementById('previousBursaryDetails'),
    previousBursaryDetailsContinued: document.getElementById('previousBursaryDetailsContinued'),
    providerNote: document.getElementById('providerNote'),
    // NEW: Containers for parent information and status
    parentInfoGroup: document.getElementById('parentInfoGroup'), 
    parentalStatusGroup: document.getElementById('parentalStatusGroup')
  };
  
  // Cache navigation buttons
  const navButtons = {
    toStep2: document.getElementById('toStep2'),
    backTo1: document.getElementById('backTo1'),
    toStep3: document.getElementById('toStep3'),
    backTo2: document.getElementById('backTo2'),
    toStep4: document.getElementById('toStep4'),
    backTo3: document.getElementById('backTo3'),
    toStep5: document.getElementById('toStep5'),
    backTo4: document.getElementById('backTo4')
  };
  
  // Cache financial and institution fields
  const financialFields = {
    annualIncome: document.getElementById('annual_family_income'),
    tuitionFee: document.getElementById('tuition_fee'),
    amountRequested: document.getElementById('amount_requested'),
    reasonForApplication: document.getElementById('reason_for_application'),
    numberOfSiblings: document.getElementById('number_of_siblings'),
    siblingsInSchool: document.getElementById('siblings_in_school')
  };

  // NEW: Cache institution level and performance labels
  const institutionFields = {
    level: form.querySelector('select[name="level"]'),
    perf1Label: document.getElementById('perf1Label'),
    perf2Label: document.getElementById('perf2Label'),
    perf3Label: document.getElementById('perf3Label')
  };


  // === STATE MANAGEMENT ===
  let currentStep = 1;
  const totalSteps = sections.length;

  // Set radio button defaults
  setRadioDefault('orphan', 'False');
  setRadioDefault('disability', 'False');
  setRadioDefault('previousBursary', 'False');
  setRadioDefault('singleParent', 'False');
  setRadioDefault('bothParentsAlive', 'True'); // Ensure a default for consistency

  // === HELPER FUNCTIONS ===
  function setRadioDefault(name, value) {
    const radio = form.querySelector(`input[name="${name}"][value="${value}"]`);
    if (radio && !form.querySelector(`input[name="${name}"]:checked`)) {
      radio.checked = true;
    }
  }

  function getRadioValue(name) {
    const checked = form.querySelector(`input[name="${name}"]:checked`);
    return checked ? checked.value : null;
  }

  function showHideConditional(element, show) {
    if (!element) return;
    
    element.classList.toggle('show', show);
    
    // Manage required attributes efficiently
    const fields = element.querySelectorAll('input, select, textarea');
    fields.forEach(field => {
      if (field.dataset.originalRequired === undefined) {
        field.dataset.originalRequired = field.hasAttribute('required') ? 'true' : 'false';
      }
      
      if (show && field.dataset.originalRequired === 'true') {
        field.setAttribute('required', 'required');
      } else {
        field.removeAttribute('required');
        // Clear value when hidden to prevent submission of unwanted data
        if (!show) {
          if (field.type === 'radio') {
            // Uncheck radios in hidden groups
            field.checked = false; 
          } else if (field.tagName === 'SELECT' || field.tagName === 'TEXTAREA' || field.type === 'text' || field.type === 'number') {
            // Clear text/number inputs
            field.value = '';
          }
        }
      }
    });
  }

  function handleConditionalFields() {
    // Get current states
    const isOrphan = getRadioValue('orphan') === 'True';
    const hasDisability = getRadioValue('disability') === 'True';
    const previousBursary = getRadioValue('previousBursary') === 'True';
    const bothParentsAlive = getRadioValue('bothParentsAlive') === 'True';
    const singleParent = getRadioValue('singleParent') === 'True';
    
    // NEW ORPHAN LOGIC: If orphan, hide parent details and parental status radios
    const showParentInfo = !isOrphan;
    showHideConditional(conditionalFields.parentInfoGroup, showParentInfo);
    showHideConditional(conditionalFields.parentalStatusGroup, showParentInfo);
    
    // Update conditional field visibility (existing logic)
    showHideConditional(conditionalFields.orphanNote, isOrphan);
    showHideConditional(conditionalFields.disabilityDetails, hasDisability);
    showHideConditional(conditionalFields.previousBursaryDetails, previousBursary);
    showHideConditional(conditionalFields.previousBursaryDetailsContinued, previousBursary);
    
    // Fee provider note should show if: Orphan OR (Parents not both alive AND is a single parent)
    // NOTE: If orphan is YES, we assume the guardian is the provider, so the note is relevant.
    const needsProviderNote = isOrphan || !showParentInfo || singleParent; 
    showHideConditional(conditionalFields.providerNote, needsProviderNote);
  }

  // === INSTITUTION LABEL HANDLER ===
  function handleInstitutionLabels() {
    const level = institutionFields.level?.value;
    // Check if the level includes 'University' or 'College' (case-insensitive)
    const isCollegeOrUniversity = level && (level.toLowerCase().includes('university') || level.toLowerCase().includes('college'));
    
    const label1 = isCollegeOrUniversity ? 'Semester 1' : 'Term 1';
    const label2 = isCollegeOrUniversity ? 'Semester 2' : 'Term 2';
    const label3 = isCollegeOrUniversity ? 'Semester 3' : 'Term 3';
    
    if (institutionFields.perf1Label) institutionFields.perf1Label.textContent = label1;
    if (institutionFields.perf2Label) institutionFields.perf2Label.textContent = label2;
    if (institutionFields.perf3Label) institutionFields.perf3Label.textContent = label3;
  }


  // === EVENT DELEGATION FOR RADIO BUTTONS AND SELECTS ===
  form.addEventListener('change', function(e) {
    if (e.target.type === 'radio') {
      handleConditionalFields();
    } else if (e.target.name === 'level') { // Check for institution level change
      handleInstitutionLabels();
    }
  });

  // Initial call
  handleConditionalFields();
  handleInstitutionLabels(); // Initial run for labels

  // === NAVIGATION FUNCTIONS ===
  function updateProgress() {
    const pct = Math.round((currentStep - 1) / (totalSteps - 1) * 100);
    progressFill.style.width = pct + '%';

    // Update step indicators
    steps.forEach((st, i) => {
      st.classList.toggle('active', i + 1 === currentStep);
    });
    
    // Hide all sections, only show current
    sections.forEach(s => {
      const step = parseInt(s.dataset.step, 10);
      s.classList.remove('active', 'completed');
      
      if (step === currentStep) {
        s.classList.add('active');
      } else if (step < currentStep) {
        s.classList.add('completed');
      }
      
      const sn = s.querySelector('.section-number');
      if (sn) sn.classList.toggle('active', step === currentStep);
    });
  }

  function goToStep(n) {
    // When going forward, validate current step
    if (n > currentStep) {
      if (!validateStep(currentStep)) return;
      
      // Additional validation for step 2
      if (currentStep === 2 && !validateFinancialFields()) return;
    }
    
    currentStep = n;
    updateProgress();
    
    // Scroll to top smoothly
    window.scrollTo({ top: 0, behavior: 'smooth' });
    
    // Clear any previous error messages when navigating
    clearMessages();
  }

  // === NAVIGATION EVENT LISTENERS ===
  if (navButtons.toStep2) navButtons.toStep2.addEventListener('click', () => goToStep(2));
  if (navButtons.backTo1) navButtons.backTo1.addEventListener('click', () => goToStep(1));
  if (navButtons.toStep3) navButtons.toStep3.addEventListener('click', () => goToStep(3));
  if (navButtons.backTo2) navButtons.backTo2.addEventListener('click', () => goToStep(2));
  if (navButtons.toStep4) navButtons.toStep4.addEventListener('click', () => goToStep(4));
  if (navButtons.backTo3) navButtons.backTo3.addEventListener('click', () => goToStep(3));
  if (navButtons.toStep5) navButtons.toStep5.addEventListener('click', () => goToStep(5));
  if (navButtons.backTo4) navButtons.backTo4.addEventListener('click', () => goToStep(4));

  // === VALIDATION FUNCTIONS ===
  function validateStep(step) {
    const sec = sections[step - 1];
    if (!sec) return false;
    
    // Only validate fields in the active section
    const requiredEls = sec.querySelectorAll('[required]');
    
    for (let el of requiredEls) {
      // Skip if element is in a hidden conditional field
      const parentConditional = el.closest('.conditional');
      if (parentConditional && !parentConditional.classList.contains('show')) {
        continue;
      }
      
      if (el.type === 'file') {
        if (el.files.length === 0) {
          showError(`Please attach required file: ${el.previousElementSibling?.textContent || 'file'}`);
          el.scrollIntoView({ behavior: 'smooth', block: 'center' });
          return false;
        }
      } else if (el.tagName === 'SELECT' && el.value === '') {
        showError("Please select all required options.");
        el.focus();
        return false;
      } else if (!el.value || el.value.trim() === '') {
        const label = el.closest('.form-group')?.querySelector('label')?.textContent.replace('*', '').trim();
        showError(`Please fill in: ${label || 'all required fields'}`);
        el.focus();
        return false;
      }
    }
    
    // Validate radio groups
    const radioGroups = sec.querySelectorAll('.form-group .radio-group');
    for (let groupDiv of radioGroups) {
      const labelEl = groupDiv.closest('.form-group')?.querySelector('label.required');

      if (labelEl) {
        const groupName = groupDiv.querySelector('input[type="radio"]')?.name;
        // Check if the radio group is visible (it's offsetParent won't be null if visible)
        if (groupName && groupDiv.offsetParent !== null) { 
          const checked = sec.querySelector(`input[name="${groupName}"]:checked`);
          const groupLabel = labelEl.textContent.replace('*', '').trim();
          
          if (!checked) {
            showError(`Please select an option for: ${groupLabel}`);
            groupDiv.closest('.form-group').classList.add('has-error');
            groupDiv.scrollIntoView({ behavior: 'smooth', block: 'center' });
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

  function validateFinancialFields() {
    const annualIncome = parseFloat(financialFields.annualIncome?.value || 0);
    const tuitionFee = parseFloat(financialFields.tuitionFee?.value || 0);
    const amountRequested = parseFloat(financialFields.amountRequested?.value || 0);
    
    if (tuitionFee <= 0) {
      showError('Tuition fee must be greater than zero.');
      financialFields.tuitionFee.focus();
      return false;
    }
    
    if (amountRequested <= 0) {
      showError('Amount requested must be greater than zero.');
      financialFields.amountRequested.focus();
      return false;
    }
    
    if (amountRequested > tuitionFee) {
      showError(`Amount requested (KES ${amountRequested.toLocaleString()}) cannot exceed tuition fee (KES ${tuitionFee.toLocaleString()}).`);
      financialFields.amountRequested.focus();
      return false;
    }
    
    if (amountRequested < tuitionFee * 0.1) {
      if (!confirm(`Amount requested (KES ${amountRequested.toLocaleString()}) is less than 10% of tuition fee. Continue?`)) {
        financialFields.amountRequested.focus();
        return false;
      }
    }
    
    if (annualIncome > tuitionFee * 10) {
      if (!confirm(`Your annual family income (KES ${annualIncome.toLocaleString()}) appears high. Please ensure your reason for application explains your need. Continue?`)) {
        financialFields.reasonForApplication.focus();
        return false;
      }
    }
    
    return true;
  }

  // === REAL-TIME VALIDATION FOR AMOUNT REQUESTED ===
  if (financialFields.amountRequested) {
    financialFields.amountRequested.addEventListener('blur', function() {
      const tuitionFee = parseFloat(financialFields.tuitionFee?.value || 0);
      const amountRequested = parseFloat(this.value || 0);
      
      if (amountRequested > tuitionFee && tuitionFee > 0) {
        showError(`Amount requested cannot exceed tuition fee of KES ${tuitionFee.toLocaleString()}`);
        this.value = '';
        this.focus();
      } else {
        clearMessages();
      }
    });
  }
  // === R6: REAL-TIME VALIDATION HELPER ===
  function validateField(el) {
    clearErrorForField(el); // Clear previous errors
    
    const parentConditional = el.closest('.conditional');
    // Skip validation if element is in a hidden conditional field
    if (parentConditional && !parentConditional.classList.contains('show')) {
      return true;
    }

    if (el.hasAttribute('required')) {
      if (el.type === 'file' && el.files.length === 0) {
        showErrorForField(el, `File required.`);
        return false;
      } else if (!el.value || el.value.trim() === '') {
        const label = el.closest('.form-group')?.querySelector('label')?.textContent.replace('*', '').trim() || 'This field';
        showErrorForField(el, `${label} is required.`);
        return false;
      }
    }
    
    // Add specific validation logic here (e.g., email format, number range)
    if (el.id === 'amount_requested') {
        const tuitionFee = parseFloat(financialFields.tuitionFee?.value || 0);
        const amountRequested = parseFloat(el.value || 0);
        if (amountRequested > tuitionFee && tuitionFee > 0) {
            showErrorForField(el, `Amount requested cannot exceed tuition fee.`);
            return false;
        }
    }

    return true;
  }
  
  function showErrorForField(el, message) {
      el.classList.add('is-invalid');
      let errorContainer = el.closest('.form-group').querySelector('.field-error-message');
      if (!errorContainer) {
          errorContainer = document.createElement('div');
          errorContainer.className = 'field-error-message error-message';
          el.closest('.form-group').appendChild(errorContainer);
      }
      errorContainer.textContent = message;
      errorContainer.style.display = 'block';
  }

  function clearErrorForField(el) {
      el.classList.remove('is-invalid');
      const errorContainer = el.closest('.form-group').querySelector('.field-error-message');
      if (errorContainer) {
          errorContainer.style.display = 'none';
      }
  }


  // === EVENT DELEGATION FOR ALL INPUTS (R6) ===
  form.addEventListener('change', function(e) {
    if (e.target.type === 'radio') {
      handleConditionalFields();
    } else if (e.target.name === 'level') { 
      handleInstitutionLabels();
    }
  });
  
  // R6: Add real-time validation on blur and keyup
  form.addEventListener('blur', function(e) {
      // Validate on blur for all inputs except radios/files
      if (e.target.tagName === 'INPUT' || e.target.tagName === 'SELECT' || e.target.tagName === 'TEXTAREA') {
          validateField(e.target);
      }
  }, true); // Use capture phase for better event handling

  form.addEventListener('keyup', function(e) {
      // Validate while typing for text/number fields
      if (e.target.type === 'text' || e.target.type === 'number' || e.target.tagName === 'TEXTAREA') {
          validateField(e.target);
      }
  });


  // ... (Rest of existing app.js logic, ensure validateStep calls validateField for all fields)
  
  function validateStep(step) {
    const sec = sections[step - 1];
    if (!sec) return false;
    
    // Validate all fields in the current step
    let isValid = true;
    
    const inputElements = sec.querySelectorAll('input, select, textarea');
    for (let el of inputElements) {
        // If validateField returns false, set isValid to false, but continue
        // to collect all errors in the step.
        if (!validateField(el)) {
            isValid = false;
        }
    }
    
    // ... (Existing radio group validation loop, using the new error helpers)
    
    if (!isValid) {
        showError('Please correct the highlighted errors before navigating.');
        // Scroll to the first invalid field
        const firstInvalid = sec.querySelector('.is-invalid');
        if (firstInvalid) {
            firstInvalid.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
    }
    
    return isValid;
  }
  // === FILE PREVIEW SETUP ===
  const fileInputs = [
    { id: 'idFile', preview: 'idFilePreview' },
    { id: 'reportForm', preview: 'reportFormPreview' },
    { id: 'parentIdFile', preview: 'parentIdFilePreview' },
    { id: 'studentIdFile', preview: 'studentIdFilePreview' },
    { id: 'instIdFile', preview: 'instIdFilePreview' },
    { id: 'instLetter', preview: 'instLetterPreview' },
    { id: 'guardianFile', preview: 'guardianFilePreview' },
    { id: 'passportPhoto', preview: 'passportPhotoPreview' }
  ];

  fileInputs.forEach(({ id, preview }) => {
    const input = document.getElementById(id);
    const previewEl = document.getElementById(preview);
    if (input && previewEl) {
      input.addEventListener('change', () => {
        const f = input.files[0];
        if (!f) {
          previewEl.innerText = '';
          return;
        }
        previewEl.innerText = `✓ ${f.name} (${Math.round(f.size / 1024)} KB)`;
        previewEl.style.color = '#006400';
      });
    }
  });

  // === FORM SUBMISSION ===
  form.addEventListener('submit', (e) => {
    e.preventDefault();
    
    console.log('Form submission started...');
    
    // Validate all steps before final submission
    for (let s = 1; s <= totalSteps; s++) {
      if (!validateStep(s)) {
        goToStep(s);
        showError('Please correct the highlighted errors before submitting.');
        submitBtn.disabled = false;
        submitBtn.textContent = 'Submit Application';
        return;
      }
    }
    
    // Disable submit button to prevent double submission
    submitBtn.disabled = true;
    submitBtn.textContent = 'Submitting...';
    
    console.log('All validations passed, submitting form...');
    
    // Submit the form
    form.submit();
  });

  // === MESSAGE FUNCTIONS ===
  function showSuccess(text) {
    successMsg.innerText = text;
    successMsg.style.display = 'block';
    errorMsg.style.display = 'none';
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  function showError(text) {
    errorMsg.innerText = text;
    errorMsg.style.display = 'block';
    successMsg.style.display = 'none';
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  function clearMessages() {
    errorMsg.style.display = 'none';
    successMsg.style.display = 'none';
  }

  // === HELP BUTTON ===
  if (helpBtn) {
    helpBtn.addEventListener('click', () => {
      alert('Need help?\n\nContact:\nEmail: bursary@westpokot.go.ke\nPhone: +254 XXX XXX XXX\n\nOffice: West Pokot County Bursary Office');
    });
  }

  // === INITIALIZE ===
  updateProgress();
  console.log('Form initialized successfully');
});