// ---------- CONFIG ----------
const SHEET_ID = 'YOUR_GOOGLE_SHEET_ID_HERE';       // <<-- set this
const DRIVE_FOLDER_ID = 'YOUR_DRIVE_FOLDER_ID_HERE';// <<-- set this
// --------------------------------------------------------------------------------

/**
 * Handle POST requests from the form frontend.
 * Expects JSON body with form fields & base64 files in payload.files.
 */
function doPost(e) {
  try {
    // parse JSON body
    const body = JSON.parse(e.postData.contents);
    const timestamp = body.timestamp || new Date().toISOString();

    // save files to Drive
    const driveFolder = DriveApp.getFolderById(DRIVE_FOLDER_ID);
    const fileUrls = {};

    if (body.files) {
      Object.keys(body.files).forEach(key => {
        const f = body.files[key];
        if (!f || !f.b64) return;
        const blob = Utilities.newBlob(Utilities.base64Decode(f.b64), f.type || 'application/octet-stream', f.name);
        const file = driveFolder.createFile(blob);
        fileUrls[key] = file.getUrl();
      });
    }

    // append to sheet
    const ss = SpreadsheetApp.openById(SHEET_ID);
    const sheet = ss.getSheets()[0];

    // create a row with main fields (adjust columns as you like)
    const row = [
      timestamp,
      body.fullName || '',
      body.idNumber || '',
      body.dob || '',
      body.gender || '',
      body.county || '',
      body.subCounty || '',
      body.phone || '',
      body.email || '',
      body.orphan || '',
      body.institution || '',
      body.level || '',
      body.course || '',
      body.yearForm || '',
      body.instContact || '',
      body.parentName || '',
      body.relation || '',
      body.parentPhone || '',
      body.parentId || '',
      body.signature || '',
      body.notes || '',
      fileUrls.idFile || '',
      fileUrls.instLetter || '',
      fileUrls.guardianFile || ''
    ];

    sheet.appendRow(row);

    return ContentService
      .createTextOutput(JSON.stringify({success:true, recordId: 'row appended'}))
      .setMimeType(ContentService.MimeType.JSON);
  } catch (err) {
    return ContentService
      .createTextOutput(JSON.stringify({success:false, error: err.toString()}))
      .setMimeType(ContentService.MimeType.JSON);
  }
}

/**
 * For convenience, allow GET to verify it's running.
 */
function doGet(e) {
  return ContentService.createTextOutput(JSON.stringify({status:'ok'})).setMimeType(ContentService.MimeType.JSON);
}
