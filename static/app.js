// Optimized bursary form with DOM caching and event delegation
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
    providerNote: document.getElementById('providerNote')
  };
  
  // Cache radio groups for faster access
  const radioGroups = {
    orphan: form.querySelectorAll('input[name="orphan"]'),
    disability: form.querySelectorAll('input[name="disability"]'),
    previousBursary: form.querySelectorAll('input[name="previousBursary"]'),
    bothParentsAlive: form.querySelectorAll('input[name="bothParentsAlive"]'),
    singleParent: form.querySelectorAll('input[name="singleParent"]')
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
  
  // Cache financial fields
  const financialFields = {
    annualIncome: document.getElementById('annual_family_income'),
    tuitionFee: document.getElementById('tuition_fee'),
    amountRequested: document.getElementById('amount_requested'),
    reasonForApplication: document.getElementById('reason_for_application'),
    numberOfSiblings: document.getElementById('number_of_siblings'),
    siblingsInSchool: document.getElementById('siblings_in_school')
  };

  // === STATE MANAGEMENT ===
  let currentStep = 1;
  const totalSteps = sections.length;

  // Set radio button defaults
  setRadioDefault('orphan', 'False');
  setRadioDefault('disability', 'False');
  setRadioDefault('previousBursary', 'False');
  setRadioDefault('singleParent', 'False');

  // === HELPER FUNCTIONS ===
  function setRadioDefault(name, value) {
    const radio = form.querySelector(`input[name="${name}"][value="${value}"]`);
    if (radio) radio.checked = true;
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
      }
    });
  }

  function handleConditionalFields() {
    // Get current states (optimized with cached elements)
    const isOrphan = getRadioValue('orphan') === 'True';
    const hasDisability = getRadioValue('disability') === 'True';
    const previousBursary = getRadioValue('previousBursary') === 'True';
    const bothParentsAlive = getRadioValue('bothParentsAlive') === 'True';
    const singleParent = getRadioValue('singleParent') === 'True';
    
    // Update conditional field visibility
    showHideConditional(conditionalFields.orphanNote, isOrphan);
    showHideConditional(conditionalFields.disabilityDetails, hasDisability);
    showHideConditional(conditionalFields.previousBursaryDetails, previousBursary);
    showHideConditional(conditionalFields.previousBursaryDetailsContinued, previousBursary);
    
    const needsProviderNote = isOrphan || !bothParentsAlive || singleParent;
    showHideConditional(conditionalFields.providerNote, needsProviderNote);
  }

  // === EVENT DELEGATION FOR RADIO BUTTONS ===
  // Instead of adding individual listeners, use one delegated listener
  form.addEventListener('change', function(e) {
    if (e.target.type === 'radio') {
      handleConditionalFields();
    }
  });

  // Initial call
  handleConditionalFields();

  // === NAVIGATION FUNCTIONS ===
  function updateProgress() {
    const pct = Math.round((currentStep - 1) / (totalSteps - 1) * 100);
    progressFill.style.width = pct + '%';

    steps.forEach((st, i) => {
      st.classList.toggle('active', i + 1 === currentStep);
    });
    
    sections.forEach(s => {
      const step = parseInt(s.dataset.step, 10);
      s.classList.toggle('active', step === currentStep);
      s.classList.toggle('completed', step < currentStep);
      const sn = s.querySelector('.section-number');
      if (sn) sn.classList.toggle('active', step === currentStep);
    });
  }

  function goToStep(n) {
    if (n > currentStep) {
      if (!validateStep(currentStep)) return;
    }
    currentStep = n;
    updateProgress();
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  // === NAVIGATION EVENT LISTENERS ===
  navButtons.toStep2.addEventListener('click', () => goToStep(2));
  navButtons.backTo1.addEventListener('click', () => goToStep(1));
  navButtons.toStep3.addEventListener('click', () => {
    if (validateStep(2) && validateFinancialFields()) {
      goToStep(3);
    }
  });
  navButtons.backTo2.addEventListener('click', () => goToStep(2));
  navButtons.toStep4.addEventListener('click', () => goToStep(4));
  navButtons.backTo3.addEventListener('click', () => goToStep(3));
  navButtons.toStep5.addEventListener('click', () => goToStep(5));
  navButtons.backTo4.addEventListener('click', () => goToStep(4));

  // === VALIDATION FUNCTIONS ===
  function validateStep(step) {
    const sec = sections[step - 1];
    if (!sec) return false;
    
    const requiredEls = sec.querySelectorAll('[required]');
    
    for (let el of requiredEls) {
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
    
    // Validate radio groups
    const radioGroups = sec.querySelectorAll('.form-group .radio-group');
    for (let groupDiv of radioGroups) {
      const labelEl = groupDiv.closest('.form-group')?.querySelector('label.required');

      if (labelEl) {
        const groupName = groupDiv.querySelector('input[type="radio"]')?.name;
        if (groupName && groupDiv.offsetParent !== null) {
          const checked = sec.querySelector(`input[name="${groupName}"]:checked`);
          const groupLabel = labelEl.textContent.replace('*', '').trim();
          
          if (!checked) {
            showError(`Please select an option for: ${groupLabel}.`);
            groupDiv.closest('.form-group').classList.add('has-error');
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

  function validateFinancialFields() {
    const annualIncome = parseFloat(financialFields.annualIncome?.value || 0);
    const tuitionFee = parseFloat(financialFields.tuitionFee?.value || 0);
    const amountRequested = parseFloat(financialFields.amountRequested?.value || 0);
    
    if (tuitionFee <= 0) {
      showError('Tuition fee must be greater than zero.');
      financialFields.tuitionFee.focus();
      return false;
    }
    
    if (amountRequested > tuitionFee) {
      showError(`Amount requested (KES ${amountRequested.toLocaleString()}) cannot exceed tuition fee (KES ${tuitionFee.toLocaleString()}).`);
      financialFields.amountRequested.focus();
      return false;
    }
    
    if (amountRequested < tuitionFee * 0.1) {
      if (!confirm(`Amount requested (KES ${amountRequested.toLocaleString()}) is less than 10% of tuition fee. Do you want to continue?`)) {
        financialFields.amountRequested.focus();
        return false;
      }
    }
    
    if (annualIncome > tuitionFee * 10) {
      if (!confirm(`Your annual family income (KES ${annualIncome.toLocaleString()}) appears sufficient for tuition. Please ensure your reason for application clearly explains your financial need. Continue?`)) {
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
        previewEl.innerText = `${f.name} (${Math.round(f.size / 1024)} KB)`;
      });
    }
  });

  // === FORM SUBMISSION ===
  form.addEventListener('submit', (e) => {
    // Validate current step
    if (!validateStep(currentStep)) {
      e.preventDefault();
      return;
    }
    
    // Validate all steps before final submission
    for (let s = 1; s <= totalSteps; s++) {
      if (!validateStep(s)) {
        e.preventDefault();
        goToStep(s);
        showError('Please correct the highlighted errors before submitting.');
        submitBtn.disabled = false;
        return;
      }
    }
    
    // Disable submit button to prevent double submission
    submitBtn.disabled = true;
    submitBtn.textContent = 'Submitting...';
    
    // Form will submit naturally
  });

  // === MESSAGE FUNCTIONS ===
  function showSuccess(text) {
    successMsg.innerText = text;
    successMsg.style.display = 'block';
    errorMsg.style.display = 'none';
  }

  function showError(text) {
    errorMsg.innerText = text;
    errorMsg.style.display = 'block';
    successMsg.style.display = 'none';
  }

  function clearMessages() {
    errorMsg.style.display = 'none';
    successMsg.style.display = 'none';
  }

  // === HELP BUTTON ===
  helpBtn.addEventListener('click', () => {
    alert('Need help? Contact the County Bursary Office or use the email/phone provided in the application instructions.');
  });

  // === KEYBOARD NAVIGATION ===
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && currentStep < totalSteps) {
      const activeElement = document.activeElement;
      // Only advance if not in textarea
      if (activeElement.tagName !== 'TEXTAREA') {
        e.preventDefault();
        goToStep(currentStep + 1);
      }
    }
  });

  // === INITIALIZE ===
  updateProgress();
});