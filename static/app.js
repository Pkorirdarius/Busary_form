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

  // Initial hide
  orphanNote.style.display = 'none';
  disabilityDetails.style.display = 'none';
  previousBursaryDetails.style.display = 'none';
  previousBursaryDetailsContinued.style.display = 'none';
  providerNote.style.display = 'none';

  // Set defaults
  document.querySelector('input[name="orphan"][value="No"]').checked = true;
  document.querySelector('input[name="disability"][value="No"]').checked = true;
  document.querySelector('input[name="previousBursary"][value="No"]').checked = true;
  document.querySelector('input[name="singleParent"][value="No"]').checked = true;

  // Show/hide conditional fields based on radio selections
  form.querySelectorAll('input[type="radio"]').forEach(radio => {
    radio.addEventListener('change', function () {
      const name = this.name;
      if (name === 'orphan') {
        orphanNote.style.display = this.value === 'Yes' ? 'block' : 'none';
        providerNote.style.display = this.value === 'Yes' ? 'block' : 'none';
      } else if (name === 'disability') {
        disabilityDetails.style.display = this.value === 'Yes' ? 'block' : 'none';
      } else if (name === 'previousBursary') {
        previousBursaryDetails.style.display = this.value === 'Yes' ? 'block' : 'none';
        previousBursaryDetailsContinued.style.display = this.value === 'Yes' ? 'block' : 'none';
      } else if (name === 'bothParentsAlive') {
        // Optional: additional trigger for providerNote if both parents not alive
        if (this.value === 'No') {
          providerNote.style.display = 'block';
        } else {
          // Only hide if orphan is also No
          if (document.querySelector('input[name="orphan"]:checked').value === 'No') {
            providerNote.style.display = 'none';
          }
        }
      }
    });
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
    clearMessages();
    return true;
  }

  // ---------- Submit handler ----------
  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    if (!validateStep(currentStep)) return;
    // final validation across all steps: ensure step 1-5 required fields present
    for (let s=1; s<=totalSteps; s++) {
      if (!validateStep(s)) {
        goToStep(s);
        return;
      }
    }

    // build payload (for local use or logging, since no send)
    const payload = {
      timestamp: new Date().toISOString(),
      fullName: document.getElementById('fullName').value.trim(),
      idNumber: document.getElementById('idNumber').value.trim(),
      dob: document.getElementById('dob').value,
      gender: document.getElementById('gender').value,
      county: document.getElementById('county').value.trim(),
      subCounty: document.getElementById('subCounty').value.trim(),
      ward: document.getElementById('ward').value.trim(),
      location: document.getElementById('location').value.trim(),
      subLocation: document.getElementById('subLocation').value.trim(),
      village: document.getElementById('village').value.trim(),
      chiefName: document.getElementById('chiefName').value.trim(),
      phone: document.getElementById('phone').value.trim(),
      email: document.getElementById('email').value.trim(),
      orphan: document.querySelector('input[name="orphan"]:checked')?.value || '',
      disability: document.querySelector('input[name="disability"]:checked')?.value || '',
      disabilityNature: document.getElementById('disabilityNature').value.trim(),
      disabilityRegNo: document.getElementById('disabilityRegNo').value.trim(),
      previousBursary: document.querySelector('input[name="previousBursary"]:checked')?.value || '',
      cdfAmount: document.getElementById('cdfAmount').value.trim(),
      ministryAmount: document.getElementById('ministryAmount').value.trim(),
      countyGovAmount: document.getElementById('countyGovAmount').value.trim(),
      otherBursary: document.getElementById('otherBursary').value.trim(),
      institution: document.getElementById('institution').value.trim(),
      level: document.getElementById('level').value,
      course: document.getElementById('course').value.trim(),
      yearForm: document.getElementById('yearForm').value.trim(),
      instCounty: document.getElementById('instCounty').value.trim(),
      instContact: document.getElementById('instContact').value.trim(),
      term1: document.getElementById('term1').value.trim(),
      term2: document.getElementById('term2').value.trim(),
      term3: document.getElementById('term3').value.trim(),
      fatherName: document.getElementById('fatherName').value.trim(),
      motherName: document.getElementById('motherName').value.trim(),
      guardianName: document.getElementById('guardianName').value.trim(),
      relation: document.getElementById('relation').value.trim(),
      fatherOccupation: document.getElementById('fatherOccupation').value.trim(),
      motherOccupation: document.getElementById('motherOccupation').value.trim(),
      parentPhone: document.getElementById('parentPhone').value.trim(),
      parentId: document.getElementById('parentId').value.trim(),
      bothParentsAlive: document.querySelector('input[name="bothParentsAlive"]:checked')?.value || '',
      singleParent: document.querySelector('input[name="singleParent"]:checked')?.value || '',
      feesProvider: document.getElementById('feesProvider').value,
      otherProvider: document.getElementById('otherProvider').value.trim(),
      signature: document.getElementById('signature').value.trim(),
      studentDate: document.getElementById('studentDate').value,
      parentSignature: document.getElementById('parentSignature').value.trim(),
      parentDate: document.getElementById('parentDate').value,
      chiefFullName: document.getElementById('chiefFullName').value.trim(),
      chiefSubLocation: document.getElementById('chiefSubLocation').value.trim(),
      chiefCounty: document.getElementById('chiefCounty').value.trim(),
      chiefSubCounty: document.getElementById('chiefSubCounty').value.trim(),
      chiefLocation: document.getElementById('chiefLocation').value.trim(),
      chiefComments: document.getElementById('chiefComments').value.trim(),
      chiefSignature: document.getElementById('chiefSignature').value.trim(),
      chiefDate: document.getElementById('chiefDate').value,
      rubberStamp: document.getElementById('rubberStamp').value.trim(),
      notes: document.getElementById('notes').value.trim(),
      files: {}
    };

    // convert files to base64 (optional, since no send, but keep for completeness)
    const fileIds = ['idFile', 'reportForm', 'parentIdFile', 'studentIdFile', 'instIdFile', 'instLetter', 'guardianFile', 'passportPhoto'];
    for (let id of fileIds) {
      const el = document.getElementById(id);
      if (el && el.files[0]) {
        const f = el.files[0];
        payload.files[id] = {name: f.name, type: f.type, b64: await fileToBase64(f)};
      }
    }

    // disable submit while "sending"
    document.getElementById('submitBtn').disabled = true;
    showProgressMessage('Submitting application...');
    try {
      // Simulate submission success without sending to any URL
      // You can console.log(payload) for debugging if needed
      console.log('Form payload:', payload);
      showSuccess('Application submitted successfully.');
      form.reset();
      // clear previews
      const previewIds = ['idFilePreview', 'reportFormPreview', 'parentIdFilePreview', 'studentIdFilePreview', 'instIdFilePreview', 'instLetterPreview', 'guardianFilePreview', 'passportPhotoPreview'];
      previewIds.forEach(id => {
        const el = document.getElementById(id);
        if (el) el.innerText = '';
      });
      goToStep(1);
    } catch (err) {
      console.error(err);
      showError('Submission failed: ' + (err.message || 'error'));
    } finally {
      document.getElementById('submitBtn').disabled = false;
    }
  });

  // ---------- Messages ----------
  const successMsg = document.getElementById('successMsg');
  const errorMsg = document.getElementById('errorMsg');
  function showSuccess(text) { successMsg.innerText = text; successMsg.style.display='block'; errorMsg.style.display='none'; }
  function showError(text) { errorMsg.innerText = text; errorMsg.style.display='block'; successMsg.style.display='none'; }
  function clearMessages() { errorMsg.style.display='none'; successMsg.style.display='none'; }
  function showProgressMessage(text) { successMsg.style.display='block'; successMsg.innerText = text; errorMsg.style.display='none'; }

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