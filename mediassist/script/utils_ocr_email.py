"""
Utility Module for OCR Functionality
Handles Gemini Vision API for discharge summary image processing

Security: API keys are loaded from secure sources:
- Environment variables (recommended for production/Kaggle)
- .streamlit/secrets.toml (local development only)
"""

import base64
import json
import re
from typing import Dict, Tuple, Optional
from io import BytesIO


def get_secure_api_key() -> str:
    """
    Get Google API key securely from environment or Streamlit secrets.
    
    Priority order:
    1. GOOGLE_API_KEY environment variable (most secure)
    2. Streamlit secrets (development only)
    
    Returns:
        API key string
        
    Raises:
        ValueError: If API key not found in any secure source
    """
    import os
    
    # Try environment variable first (most secure)
    api_key = os.getenv('GOOGLE_API_KEY')
    if api_key:
        return api_key
    
    # Try Streamlit secrets (development only)
    try:
        import streamlit as st
        if hasattr(st, 'secrets') and st.secrets:
            if 'GOOGLE_API_KEY' in st.secrets:
                return st.secrets['GOOGLE_API_KEY']
    except (ImportError, Exception):
        pass
    
    # API key not found
    raise ValueError(
        "Google API key not found. Please set it using one of these methods:\n"
        "1. Environment variable: export GOOGLE_API_KEY='your-key'\n"
        "2. Streamlit secrets: Add GOOGLE_API_KEY to .streamlit/secrets.toml\n"
        "3. For Kaggle: Use Kaggle's Secrets Manager"
    )


def compress_image(image_file, max_width: int = 1024, max_height: int = 1024) -> bytes:
    """
    Compress and resize image to reduce token usage
    
    Args:
        image_file: Uploaded image file
        max_width: Maximum width in pixels
        max_height: Maximum height in pixels
        
    Returns:
        Compressed image bytes
    """
    try:
        from PIL import Image
        
        # Read image
        image = Image.open(image_file)
        
        # Resize if too large
        image.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
        
        # Convert to RGB if necessary
        if image.mode in ('RGBA', 'LA', 'P'):
            background = Image.new('RGB', image.size, (255, 255, 255))
            background.paste(image, mask=image.split()[-1] if image.mode == 'RGBA' else None)
            image = background
        
        # Save to bytes with compression
        output = BytesIO()
        image.save(output, format='JPEG', quality=85, optimize=True)
        output.seek(0)
        return output.getvalue()
    except ImportError:
        # If Pillow not available, return original
        image_file.seek(0)
        return image_file.read()


def encode_image_to_base64(image_bytes: bytes) -> str:
    """Convert image bytes to base64 for Gemini API"""
    return base64.b64encode(image_bytes).decode('utf-8')


def extract_discharge_summary_from_image(image_file, google_api_key: Optional[str] = None) -> Tuple[bool, Dict]:
    """
    Extract discharge summary data from medical document image using Gemini Vision API
    
    Args:
        image_file: Uploaded image file from Streamlit
        google_api_key: (Optional) Google API key for Gemini. If not provided, uses get_secure_api_key()
        
    Returns:
        Tuple of (success: bool, data: Dict)
    """
    try:
        import google.generativeai as genai
        
        # Get API key if not provided
        if not google_api_key:
            google_api_key = get_secure_api_key()
        
        # Configure Gemini API
        genai.configure(api_key=google_api_key)
        model = genai.GenerativeModel('gemini-2.0-flash')
        
        # Compress image to reduce token usage (fixes token limit error)
        compressed_bytes = compress_image(image_file)
        
        # Create prompt for discharge summary extraction
        extraction_prompt = """Extract medical information from this image. Return ONLY a JSON object, no other text.

{
    "raw_text": "ALL visible text in the image",
    "patient_id": "ID if visible",
    "patient_name": "Name if visible",
    "age": "Age as number",
    "sex": "M/F",
    "admission_date": "Date if visible",
    "discharge_date": "Date if visible",
    "primary_diagnosis": "Main diagnosis",
    "secondary_diagnoses": [],
    "hospital_course": "Hospital stay summary",
    "discharge_instructions": "Instructions",
    "medications": [],
    "follow_up": [],
    "allergies": [],
    "precautions": [],
    "contact_email": "Email if visible",
    "phone": "Phone if visible"
}

Use null for empty fields. Return ONLY JSON."""
        
        # Call Gemini Vision API - pass image as bytes, not base64 string
        response = model.generate_content([
            extraction_prompt,
            {
                'mime_type': 'image/jpeg',
                'data': compressed_bytes
            }
        ])
        
        # Parse response
        response_text = response.text.strip()
        
        # Try multiple methods to extract JSON
        extracted_data = None
        
        # Method 1: Direct JSON parse
        try:
            extracted_data = json.loads(response_text)
        except json.JSONDecodeError:
            pass
        
        # Method 2: Find JSON object with regex
        if not extracted_data:
            json_match = re.search(r'\{[\s\S]*\}', response_text)
            if json_match:
                try:
                    extracted_data = json.loads(json_match.group())
                except json.JSONDecodeError:
                    pass
        
        # Method 3: Clean common JSON issues and retry
        if not extracted_data:
            # Remove markdown code blocks if present
            cleaned = response_text.replace('```json', '').replace('```', '')
            try:
                extracted_data = json.loads(cleaned)
            except json.JSONDecodeError:
                pass
        
        # If we still don't have data, return detailed error
        if not extracted_data:
            return False, {
                "error": f"Could not parse JSON from response. Raw response: {response_text[:300]}",
                "debugging": "The model may have returned text instead of JSON. Check if the image is readable."
            }
        
        # Convert age to int if possible
        if extracted_data.get("age"):
            try:
                extracted_data["age"] = int(extracted_data["age"])
            except (ValueError, TypeError):
                extracted_data["age"] = 0
        
        # Debug: Check if we got raw_text which indicates model saw the image
        raw_text = extracted_data.get("raw_text", "")
        if not raw_text or raw_text.lower() in ["", "null", "none"]:
            return False, {
                "error": "Model could not read text from image. Image may be too blurry, low quality, or not a medical document.",
                "extracted_data": extracted_data
            }
        
        return True, extracted_data
            
    except ImportError:
        return False, {"error": "google-generativeai package not installed. Install with: pip install google-generativeai"}
    except Exception as e:
        return False, {"error": f"OCR Error: {str(e)}"}

