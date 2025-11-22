"""
API Key Configuration Manager - Secure Credential Handling
===========================================================

This module handles API key management securely:
1. Reads from environment variables (preferred)
2. Falls back to .streamlit/secrets.toml (local dev only)
3. Provides graceful error messages for missing keys
4. Never logs or exposes API keys
5. Validates configuration at startup

Usage:
    from config_api_keys import get_api_key, validate_api_keys
    
    api_key = get_api_key('GOOGLE_API_KEY')
    validate_api_keys()  # Check all required keys at startup
"""

import os
import sys
from typing import Optional, Dict, List
import logging

logger = logging.getLogger(__name__)


class APIKeyError(Exception):
    """Exception raised when API key is missing or invalid."""
    pass


class APIKeyManager:
    """Secure API Key Manager for MediSync."""
    
    # List of required API keys for the application
    REQUIRED_KEYS = {
        'GOOGLE_API_KEY': {
            'name': 'Google Generative AI',
            'source': 'https://ai.google.dev/',
            'description': 'For discharge summary image OCR'
        }
    }
    
    # Optional keys for future features
    OPTIONAL_KEYS = {
        # 'ANOTHER_API_KEY': {...}
    }
    
    def __init__(self):
        """Initialize the API Key Manager."""
        self._cache: Dict[str, Optional[str]] = {}
        self._tried_streamlit_secrets = False
    
    def get_api_key(self, key_name: str, raise_error: bool = False) -> Optional[str]:
        """
        Retrieve an API key from secure sources.
        
        Sources checked in order:
        1. Environment variables
        2. .streamlit/secrets.toml (local development only)
        3. Returns None if not found
        
        Args:
            key_name: Name of the API key (e.g., 'GOOGLE_API_KEY')
            raise_error: If True, raise APIKeyError if key not found
            
        Returns:
            API key value or None if not found
            
        Raises:
            APIKeyError: If raise_error=True and key not found
        """
        # Check cache
        if key_name in self._cache:
            return self._cache[key_name]
        
        # Try environment variable first (most secure)
        api_key = os.getenv(key_name)
        
        # Try Streamlit secrets only if env var not found
        if not api_key:
            api_key = self._get_from_streamlit_secrets(key_name)
        
        # Cache the result
        self._cache[key_name] = api_key
        
        # Handle missing key
        if not api_key:
            if raise_error:
                self._raise_key_error(key_name)
            else:
                logger.warning(f"API key not found: {key_name}")
                return None
        
        return api_key
    
    def _get_from_streamlit_secrets(self, key_name: str) -> Optional[str]:
        """
        Try to get API key from Streamlit secrets (local development only).
        
        Note: This should NEVER work in production or public repositories.
        """
        try:
            import streamlit as st
            
            # Check if running in Streamlit context
            if hasattr(st, 'secrets') and st.secrets:
                # Try different formats
                if key_name in st.secrets:
                    return st.secrets[key_name]
                
                # Try with google prefix
                if 'google_api' in st.secrets:
                    if 'api_key' in st.secrets['google_api']:
                        return st.secrets['google_api']['api_key']
                    if key_name == 'GOOGLE_API_KEY':
                        return st.secrets['google_api'].get('api_key')
            
        except Exception as e:
            logger.debug(f"Could not read from Streamlit secrets: {str(e)}")
        
        return None
    
    def validate_api_keys(self, raise_errors: bool = False) -> Dict[str, bool]:
        """
        Validate that all required API keys are available.
        
        Args:
            raise_errors: If True, raise error on first missing key
            
        Returns:
            Dictionary with key names and availability status
        """
        validation_results = {}
        
        for key_name, key_info in self.REQUIRED_KEYS.items():
            api_key = self.get_api_key(key_name, raise_error=False)
            is_present = api_key is not None
            validation_results[key_name] = is_present
            
            status = "✓ Found" if is_present else "✗ Missing"
            logger.info(f"{key_name}: {status}")
            
            if not is_present and raise_errors:
                self._raise_key_error(key_name)
        
        return validation_results
    
    def _raise_key_error(self, key_name: str) -> None:
        """Raise a detailed API key error with setup instructions."""
        key_info = self.REQUIRED_KEYS.get(key_name, {})
        
        error_message = f"""
        
╔════════════════════════════════════════════════════════════════╗
║              MISSING API KEY: {key_name:<40} ║
╠════════════════════════════════════════════════════════════════╣
║                                                                ║
║ The required API key '{key_name}' is not configured.          ║
║                                                                ║
║ Description: {key_info.get('description', 'N/A'):<46}║
║                                                                ║
║ ──────────────────────────────────────────────────────────── ║
║ SETUP INSTRUCTIONS:                                            ║
║ ──────────────────────────────────────────────────────────── ║
║                                                                ║
║ 1. GET YOUR API KEY:                                          ║
║    Visit: {key_info.get('source', 'N/A'):<49}║
║                                                                ║
║ 2. SET ENVIRONMENT VARIABLE (Recommended):                    ║
║    • Linux/macOS: export {key_name}="your-key"              ║
║    • Windows: set {key_name}=your-key                        ║
║    • Python: os.environ['{key_name}'] = 'your-key'          ║
║                                                                ║
║ 3. OR USE STREAMLIT SECRETS (Local Development Only):        ║
║    • Create .streamlit/secrets.toml                           ║
║    • Add: {key_name} = "your-key"                           ║
║    • DO NOT commit secrets.toml to GitHub                     ║
║                                                                ║
║ 4. FOR KAGGLE NOTEBOOKS:                                      ║
║    • Use Kaggle's Secrets Manager                             ║
║    • Settings > Secrets > Add Secret                          ║
║    • Name: {key_name}                                        ║
║                                                                ║
║ ⚠️  SECURITY WARNING:                                          ║
║    • Never hardcode API keys in source code                   ║
║    • Never commit secrets.toml to version control             ║
║    • Ensure .gitignore includes .streamlit/secrets.toml       ║
║                                                                ║
╚════════════════════════════════════════════════════════════════╝
        """
        
        raise APIKeyError(error_message)
    
    def get_all_keys_status(self) -> str:
        """Get formatted status of all API keys."""
        print("\n" + "="*70)
        print("API KEY CONFIGURATION STATUS")
        print("="*70)
        
        print("\n📋 REQUIRED KEYS:")
        for key_name, key_info in self.REQUIRED_KEYS.items():
            api_key = self.get_api_key(key_name, raise_error=False)
            status = "✓ Configured" if api_key else "✗ Missing"
            print(f"  {status:<20} {key_name:<30} ({key_info['description']})")
        
        print("\n📋 OPTIONAL KEYS:")
        if self.OPTIONAL_KEYS:
            for key_name in self.OPTIONAL_KEYS:
                api_key = self.get_api_key(key_name, raise_error=False)
                status = "✓ Configured" if api_key else "○ Not Configured"
                print(f"  {status:<20} {key_name}")
        else:
            print("  (None configured yet)")
        
        print("\n" + "="*70 + "\n")


# Global instance
_manager: Optional[APIKeyManager] = None


def get_api_key(key_name: str, raise_error: bool = False) -> Optional[str]:
    """
    Get an API key by name.
    
    Example:
        api_key = get_api_key('GOOGLE_API_KEY')
    """
    global _manager
    if _manager is None:
        _manager = APIKeyManager()
    return _manager.get_api_key(key_name, raise_error=raise_error)


def validate_api_keys(raise_errors: bool = False) -> Dict[str, bool]:
    """
    Validate all required API keys are available.
    
    Example:
        validate_api_keys()  # Will raise if any key missing
    """
    global _manager
    if _manager is None:
        _manager = APIKeyManager()
    return _manager.validate_api_keys(raise_errors=raise_errors)


def show_api_key_status() -> None:
    """Show status of all API keys."""
    global _manager
    if _manager is None:
        _manager = APIKeyManager()
    _manager.get_all_keys_status()
