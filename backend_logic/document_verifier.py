# backend_logic/document_verifier.py

import re
import logging
import os
import tempfile
from datetime import datetime
from typing import Dict, Optional, Tuple
from difflib import SequenceMatcher
from django.core.files.uploadedfile import UploadedFile

# Optional imports - gracefully handle if not installed
try:
    from PIL import Image
    import pytesseract
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False
    
try:
    from pdf2image import convert_from_path
    PDF_SUPPORT = True
except ImportError:
    PDF_SUPPORT = False

logger = logging.getLogger(__name__)


class DocumentVerifier:
    """
    Verifies uploaded documents against form data.
    Extracts text from ID cards and birth certificates using OCR.
    """
    
    def __init__(self):
        self.ocr_available = OCR_AVAILABLE
        self.pdf_support = PDF_SUPPORT
        
        # Kenyan ID number pattern: 7-9 digits
        self.id_pattern = re.compile(r'\b\d{7,9}\b')
        
        # Name patterns (support multiple formats, generally capitalized words)
        self.name_patterns = [
            # Looks for NAME or FULL NAME followed by capitalized words (A-Z\s)
            re.compile(r'(?:NAME|FULL NAME|NAMES)[\s:]+([A-Z\s]+)', re.IGNORECASE),
            # Catches sequences of CapitalizedWord followed by CapitalizedWord
            re.compile(r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)'),
        ]
        
        # Date patterns (support multiple formats)
        self.date_patterns = [
            # Looks for DATE OF BIRTH/DOB/BORN followed by date string
            re.compile(r'(?:DATE OF BIRTH|DOB|BORN)[\s:]+([\d./-]{6,10})', re.IGNORECASE),
            # Catches standalone date strings with common separators
            re.compile(r'\b([\d./-]{6,10})\b'),
        ]
    
    def verify_document(
        self, 
        document_file: UploadedFile, 
        expected_name: str, 
        expected_id: str, 
        expected_dob: Optional[datetime] = None
    ) -> Dict[str, any]:
        """
        Main verification method.
        """
        result = {
            'success': False,
            'verified': False,
            'confidence': 0.0,
            'extracted_data': {},
            'matches': {},
            'errors': [],
            'warnings': []
        }
        
        if not self.ocr_available:
            result['errors'].append('OCR not available. Install pytesseract and Pillow.')
            result['warnings'].append('Document verification skipped - manual review required.')
            return result
        
        # Ensure file pointer is at the beginning before reading (Robustness)
        try:
            document_file.seek(0)
        except Exception as e:
            result['errors'].append(f'Failed to seek to file start: {str(e)}')
            return result
            
        try:
            # Extract text from document
            extracted_text = self._extract_text(document_file)
            
            if not extracted_text:
                result['errors'].append('Could not extract text from document.')
                return result
            
            # Extract information
            extracted_data = self._extract_information(extracted_text)
            result['extracted_data'] = extracted_data
            
            # Verify each field
            matches = {}
            
            # Verify ID number
            if expected_id and extracted_data.get('id_numbers'):
                id_match = self._verify_id_number(expected_id, extracted_data['id_numbers'])
                matches['id_number'] = id_match
            
            # Verify name (IMPROVED FUZZY MATCHING)
            if expected_name and extracted_data.get('names'):
                name_match = self._verify_name(expected_name, extracted_data['names'])
                matches['name'] = name_match
            
            # Verify date of birth (IMPROVED DATE PARSING)
            if expected_dob and extracted_data.get('dates'):
                dob_match = self._verify_dob(expected_dob, extracted_data['dates'])
                matches['dob'] = dob_match
            
            result['matches'] = matches
            
            # Calculate overall confidence
            if matches:
                # Use a balanced score (e.g., mean of available critical fields)
                critical_scores = [
                    m['confidence'] for k, m in matches.items() 
                    if isinstance(m, dict) and k in ('id_number', 'name', 'dob')
                ]
                result['confidence'] = sum(critical_scores) / len(critical_scores) if critical_scores else 0.0
            
            # Determine if verified
            result['verified'] = result['confidence'] >= 0.8  # Higher 80% threshold for critical data
            result['success'] = True
            
            # Add warnings for low confidence
            if result['confidence'] < 0.8:
                result['warnings'].append(
                    f'Low confidence match ({result["confidence"]:.1%}). Manual review recommended.'
                )
            
        except Exception as e:
            logger.error(f'Document verification error: {e}', exc_info=True)
            result['errors'].append(f'Verification error: {str(e)}')
        
        return result
    
    def _extract_text(self, document_file: UploadedFile) -> str:
        """Extract text from image or PDF document."""
        try:
            file_extension = document_file.name.lower().split('.')[-1]
            
            if file_extension == 'pdf':
                return self._extract_from_pdf(document_file)
            elif file_extension in ['jpg', 'jpeg', 'png', 'tif', 'tiff']:
                return self._extract_from_image(document_file)
            else:
                logger.warning(f'Unsupported file type: {file_extension}')
                return ''
                
        except Exception as e:
            logger.error(f'Text extraction error: {e}')
            return ''
    
    def _extract_from_image(self, image_file: UploadedFile) -> str:
        """Extract text from image using OCR with basic preprocessing."""
        try:
            image = Image.open(image_file)
            
            # --- IMPROVEMENT: Basic Preprocessing for better OCR ---
            # 1. Convert to grayscale
            gray_image = image.convert('L') 
            
            # 2. Tesseract config for structured documents (Page Segmentation Mode 6)
            custom_config = r'--oem 3 --psm 6' 
            text = pytesseract.image_to_string(gray_image, lang='eng', config=custom_config)
            return text
        except Exception as e:
            logger.error(f'Image OCR error: {e}')
            return ''
    
    def _extract_from_pdf(self, pdf_file: UploadedFile) -> str:
        """Extract text from PDF (first page only) using secure temp file handling."""
        if not self.pdf_support:
            logger.warning('PDF support not available')
            return ''
        
        tmp_path = None
        try:
            # --- CRITICAL IMPROVEMENT: Secure and guaranteed temp file handling ---
            pdf_file.seek(0) # Ensure reading from start
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
                tmp_file.write(pdf_file.read())
                tmp_path = tmp_file.name
            
            if tmp_path:
                # Convert first page to image with higher DPI for better OCR
                images = convert_from_path(tmp_path, first_page=1, last_page=1, dpi=300)
                
                if images:
                    custom_config = r'--oem 3 --psm 6'
                    text = pytesseract.image_to_string(images[0], lang='eng', config=custom_config)
                    return text
            
            return ''
            
        except Exception as e:
            logger.error(f'PDF OCR error: {e}')
            return ''
        finally:
            # --- Ensure cleanup even if exceptions occur ---
            if tmp_path and os.path.exists(tmp_path):
                try:
                    os.unlink(tmp_path)
                except Exception as e:
                    logger.error(f'Failed to delete temporary file {tmp_path}: {e}')
    
    def _extract_information(self, text: str) -> Dict[str, list]:
        """Extract structured information from text."""
        # ... (Extraction logic remains the same)
        extracted = {
            'id_numbers': [],
            'names': [],
            'dates': []
        }
        
        # Extract ID numbers
        id_matches = self.id_pattern.findall(text)
        extracted['id_numbers'] = list(set(id_matches))
        
        # Extract names
        for pattern in self.name_patterns:
            name_matches = pattern.findall(text)
            extracted['names'].extend(name_matches)
        
        # Clean and deduplicate names
        cleaned_names = []
        for name in extracted['names']:
            # Normalize and remove common trailing characters or typos
            cleaned = name.strip().upper().replace(':', '').replace('|', '').replace('.', '')
            cleaned = " ".join(cleaned.split()) # Normalize internal spacing
            if cleaned and len(cleaned) > 3 and cleaned not in cleaned_names:
                cleaned_names.append(cleaned)
        extracted['names'] = cleaned_names
        
        # Extract dates
        for pattern in self.date_patterns:
            date_matches = pattern.findall(text)
            extracted['dates'].extend(date_matches)
        
        return extracted
    
    def _verify_id_number(self, expected: str, extracted_ids: list) -> Dict:
        """Verify ID number match."""
        # ... (Logic remains largely the same, it was already good)
        expected_clean = expected.strip().replace(' ', '')
        
        best_match = None
        best_ratio = 0.0
        
        for extracted_id in extracted_ids:
            extracted_clean = extracted_id.strip().replace(' ', '')
            
            # Exact Match
            if expected_clean == extracted_clean:
                return {
                    'matched': True,
                    'confidence': 1.0,
                    'extracted_value': extracted_id,
                    'expected_value': expected
                }
            
            # Fuzzy Check
            ratio = SequenceMatcher(None, expected_clean, extracted_clean).ratio()
            if ratio > best_ratio:
                best_ratio = ratio
                best_match = extracted_id
        
        if best_match and best_ratio >= 0.8: # Accept partial match above 80%
            return {
                'matched': True,
                'confidence': best_ratio,
                'extracted_value': best_match,
                'expected_value': expected,
                'warning': 'Partial match - verify manually' if best_ratio < 1.0 else None
            }
        
        return {
            'matched': False,
            'confidence': 0.0,
            'extracted_value': extracted_ids[0] if extracted_ids else None,
            'expected_value': expected
        }
    
    def _verify_name(self, expected: str, extracted_names: list) -> Dict:
        """Verify name match using SequenceMatcher for robust fuzzy matching."""
        
        # Normalize: Upper case and remove extra spaces
        expected_clean = " ".join(expected.strip().upper().split()) 
        
        best_match = None
        best_confidence = 0.0
        
        for extracted_name in extracted_names:
            extracted_clean = " ".join(extracted_name.strip().upper().split())
            
            # --- IMPROVEMENT: SequenceMatcher for single, robust similarity score ---
            ratio = SequenceMatcher(None, expected_clean, extracted_clean).ratio()
            
            if ratio > best_confidence:
                best_confidence = ratio
                best_match = extracted_name
        
        matched = best_confidence >= 0.85 # High threshold (85%) for critical name match
        
        return {
            'matched': matched,
            'confidence': best_confidence,
            'extracted_value': best_match,
            'expected_value': expected,
            'warning': 'Name partially matched - verify spelling' if matched and best_confidence < 1.0 else None
        }
    
    def _verify_dob(self, expected: datetime, extracted_dates: list) -> Dict:
        """Verify date of birth with expanded format support."""
        expected_date = expected.date() if isinstance(expected, datetime) else expected
        
        # --- IMPROVEMENT: Expanded date formats for robustness ---
        date_formats = [
            '%d/%m/%Y', '%d-%m-%Y', '%d.%m.%Y',  # DD/MM/YYYY (Full Year)
            '%m/%d/%Y', '%m-%d-%Y', '%m.%d.%Y',  # MM/DD/YYYY (US-like)
            '%Y/%m/%d', '%Y-%m-%d', '%Y.%m.%d',  # YYYY/MM/DD (ISO-like)
            '%d/%m/%y', '%d-%m/%y', '%d.%m.%y',  # DD/MM/YY (Short Year)
        ]
        
        for date_str in extracted_dates:
            # Clean up the string to harmonize separators for parsing
            normalized_date_str = date_str.replace('.', '-').replace('/', '-')
            
            for fmt in date_formats:
                # Use the normalized string for parsing if the format uses '-'
                parse_str = normalized_date_str if '-' in fmt else date_str
                
                try:
                    parsed_date = datetime.strptime(parse_str, fmt).date()
                    
                    if parsed_date == expected_date:
                        return {
                            'matched': True,
                            'confidence': 1.0,
                            'extracted_value': date_str,
                            'expected_value': expected_date.strftime('%Y-%m-%d')
                        }
                except ValueError:
                    continue
        
        return {
            'matched': False,
            'confidence': 0.0,
            'extracted_value': extracted_dates[0] if extracted_dates else None,
            'expected_value': expected_date.strftime('%Y-%m-%d')
        }
    
    def is_available(self) -> Tuple[bool, str]:
        """Check if document verification is available."""
        if not self.ocr_available:
            return False, 'OCR libraries not installed. Install: pip install pytesseract Pillow'
        
        # Try to check if tesseract is installed
        try:
            # Check version silently
            pytesseract.get_tesseract_version()
            return True, 'Document verification available'
        except Exception as e:
            return False, f'Tesseract OCR not installed or not in PATH: {str(e)}. You may need to install it system-wide.'


# Singleton instance
_verifier = None

def get_document_verifier() -> DocumentVerifier:
    """Get or create document verifier instance."""
    global _verifier
    if _verifier is None:
        _verifier = DocumentVerifier()
    return _verifier