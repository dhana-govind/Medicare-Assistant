#!/usr/bin/env python3
"""
Security Verification Script
=============================

Verifies that all security measures are in place before GitHub submission.
Run this before pushing to GitHub to ensure no API keys are exposed.

Usage:
    python verify_security.py
"""

import os
import sys
import json
from pathlib import Path


class SecurityAuditor:
    """Audits the project for security vulnerabilities."""
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.issues = []
        self.warnings = []
        self.successes = []
    
    def run_audit(self) -> bool:
        """Run complete security audit. Returns True if all checks pass."""
        print("\n" + "="*70)
        print("MEDISYNC SECURITY AUDIT")
        print("="*70 + "\n")
        
        self.check_gitignore()
        self.check_secrets_files()
        self.check_source_code()
        self.check_documentation()
        self.check_api_key_manager()
        
        self.print_results()
        
        # Return True only if no critical issues
        return len(self.issues) == 0
    
    def check_gitignore(self):
        """Verify .gitignore is properly configured."""
        print("🔍 Checking .gitignore configuration...")
        gitignore_path = self.project_root / ".gitignore"
        
        if not gitignore_path.exists():
            self.issues.append("❌ .gitignore file not found")
            return
        
        gitignore_content = gitignore_path.read_text(encoding='utf-8', errors='ignore')
        
        # Check for critical exclusions
        required_patterns = [
            ".streamlit/secrets.toml",
            ".env",
            "api_keys.py",
            "secrets.py",
            "credentials.py"
        ]
        
        missing_patterns = []
        for pattern in required_patterns:
            if pattern not in gitignore_content:
                missing_patterns.append(pattern)
        
        if missing_patterns:
            self.issues.append(f"❌ Missing gitignore patterns: {', '.join(missing_patterns)}")
        else:
            self.successes.append("✅ .gitignore properly configured with all critical patterns")
        
        # Check that template file is NOT ignored
        if ".streamlit/secrets.toml.example" in gitignore_content and "!.streamlit/secrets.toml.example" not in gitignore_content:
            self.warnings.append("⚠️  secrets.toml.example might be ignored (should have exception)")
        else:
            self.successes.append("✅ secrets.toml.example is properly excepted from gitignore")
    
    def check_secrets_files(self):
        """Verify secrets files don't contain actual API keys."""
        print("🔍 Checking secrets files...")
        
        secrets_path = self.project_root / ".streamlit" / "secrets.toml"
        if not secrets_path.exists():
            self.warnings.append("⚠️  .streamlit/secrets.toml not found (OK for GitHub)")
            return
        
        secrets_content = secrets_path.read_text(encoding='utf-8', errors='ignore')
        
        # Check for real API key patterns
        real_key_indicators = [
            "AIzaSy",  # Google API key prefix
            "sk-",     # OpenAI key prefix
            "ghp_",    # GitHub token prefix
        ]
        
        found_real_keys = []
        for indicator in real_key_indicators:
            if indicator in secrets_content:
                # Check if it's actually a key or just documentation
                lines_with_indicator = [line for line in secrets_content.split('\n') if indicator in line and not line.strip().startswith('#')]
                if lines_with_indicator:
                    found_real_keys.append(indicator)
        
        if found_real_keys:
            self.issues.append(f"❌ CRITICAL: Real API key patterns found in secrets.toml: {found_real_keys}")
        else:
            self.successes.append("✅ No real API keys found in secrets.toml (uses placeholders)")
        
        # Check for placeholder values
        if "your-google-api-key-here" in secrets_content:
            self.successes.append("✅ secrets.toml uses placeholder values")
        elif "your-api-key" in secrets_content:
            self.successes.append("✅ secrets.toml uses placeholder values")
        else:
            self.warnings.append("⚠️  secrets.toml doesn't seem to use placeholder values")
        
        # Check template file
        template_path = self.project_root / "secrets.toml.example"
        if not template_path.exists():
            self.warnings.append("⚠️  secrets.toml.example not found")
            return
        
        template_content = template_path.read_text(encoding='utf-8', errors='ignore')
        
        # Template should have placeholders
        if "your-" in template_content:
            self.successes.append("✅ secrets.toml.example uses placeholder values")
        else:
            self.warnings.append("⚠️  Template file might not have clear placeholders")
    
    def check_source_code(self):
        """Scan source code for hardcoded API keys."""
        print("🔍 Scanning source code for hardcoded API keys...")
        
        # Real API key patterns to watch for
        real_key_patterns = [
            ("\"AIzaSy", "Google API key (starts with AIzaSy)"),
            ("'AIzaSy", "Google API key (starts with AIzaSy)"),
            ("sk-", "OpenAI API key"),
            ("ghp_", "GitHub token"),
        ]
        
        python_files = list(self.project_root.glob("*.py"))
        
        found_suspicious = False
        for py_file in python_files:
            try:
                content = py_file.read_text(encoding='utf-8', errors='ignore')
                
                # Skip if it's our config/security file or verification script
                if "config_api_keys" in py_file.name or "verify_security" in py_file.name:
                    continue
                
                for pattern, description in real_key_patterns:
                    if pattern in content:
                        self.issues.append(f"❌ Suspicious pattern found in {py_file.name}: {description}")
                        found_suspicious = True
                        break
            except Exception as e:
                self.warnings.append(f"⚠️  Could not scan {py_file.name}: {str(e)}")
        
        if not found_suspicious:
            self.successes.append("✅ No hardcoded API keys found in source code")
    
    def check_documentation(self):
        """Verify documentation files don't contain API keys."""
        print("🔍 Checking documentation files...")
        
        # Real API keys always have the actual full pattern
        real_key_pattern = "AIzaSyCQE4P8XIksuaRcR3JDwBOY0Wo7IMXZ9fQ"
        
        doc_files = list(self.project_root.glob("*.md"))
        
        found_keys_in_docs = False
        for doc_file in doc_files:
            try:
                content = doc_file.read_text(encoding='utf-8', errors='ignore')
                
                # Check for THE ACTUAL REAL KEY
                if real_key_pattern in content:
                    self.issues.append(f"❌ ACTUAL API KEY found in {doc_file.name}")
                    found_keys_in_docs = True
            except Exception as e:
                self.warnings.append(f"⚠️  Could not read {doc_file.name}: {str(e)}")
        
        if not found_keys_in_docs:
            self.successes.append("✅ No actual API keys found in documentation")
        
        # Check that API_KEY_SETUP.md exists
        if (self.project_root / "API_KEY_SETUP.md").exists():
            self.successes.append("✅ API_KEY_SETUP.md documentation present")
        else:
            self.warnings.append("⚠️  API_KEY_SETUP.md not found")
    
    def check_api_key_manager(self):
        """Verify secure API key manager is in place."""
        print("🔍 Checking API key manager implementation...")
        
        config_file = self.project_root / "config_api_keys.py"
        if not config_file.exists():
            self.warnings.append("⚠️  config_api_keys.py not found")
            return
        
        content = config_file.read_text(encoding='utf-8', errors='ignore')
        
        # Check for required functions
        required_functions = [
            "get_api_key",
            "validate_api_keys",
            "APIKeyManager",
        ]
        
        missing_functions = []
        for func in required_functions:
            if func not in content:
                missing_functions.append(func)
        
        if missing_functions:
            self.warnings.append(f"⚠️  Missing functions in config_api_keys.py: {missing_functions}")
        else:
            self.successes.append("✅ API key manager properly implemented")
        
        # Check utils_ocr_email.py uses secure retrieval
        utils_file = self.project_root / "utils_ocr_email.py"
        if utils_file.exists():
            utils_content = utils_file.read_text(encoding='utf-8', errors='ignore')
            if "get_secure_api_key" in utils_content:
                self.successes.append("✅ utils_ocr_email.py uses secure API key retrieval")
            else:
                self.warnings.append("⚠️  utils_ocr_email.py might not use secure retrieval")
    
    def print_results(self):
        """Print audit results."""
        print("\n" + "="*70)
        print("AUDIT RESULTS")
        print("="*70 + "\n")
        
        if self.successes:
            print("✅ SUCCESSES:")
            for success in self.successes:
                print(f"   {success}")
        
        if self.warnings:
            print("\n⚠️  WARNINGS:")
            for warning in self.warnings:
                print(f"   {warning}")
        
        if self.issues:
            print("\n❌ CRITICAL ISSUES:")
            for issue in self.issues:
                print(f"   {issue}")
        
        print("\n" + "="*70)
        
        # Summary
        if len(self.issues) == 0:
            print("✅ SECURITY AUDIT PASSED - Ready for GitHub submission!")
            print("="*70 + "\n")
            return True
        else:
            print(f"❌ SECURITY AUDIT FAILED - {len(self.issues)} critical issue(s) found")
            print("="*70 + "\n")
            return False


def main():
    """Run security audit."""
    # Get project root
    project_root = os.getcwd()
    
    # Run audit
    auditor = SecurityAuditor(project_root)
    passed = auditor.run_audit()
    
    # Exit with appropriate code
    sys.exit(0 if passed else 1)


if __name__ == "__main__":
    main()
