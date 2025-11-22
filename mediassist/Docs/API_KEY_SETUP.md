# API Key Security Setup Guide

## Overview

This document explains how to securely configure API keys for the MediSync application. This is **critical** for GitHub submission and Kaggle compliance.

**⚠️ Important:** Kaggle explicitly states: *"DO NOT INCLUDE ANY API KEYS OR PASSWORDS IN YOUR CODE"*

---

## Security Approach

We use a **multi-layered approach** to prevent accidental API key exposure:

1. **`.gitignore`** - Prevents committing secret files
2. **`secrets.toml.example`** - Template file showing structure (no actual values)
3. **Environment Variables** - Secure method for Kaggle and production
4. **Streamlit Secrets** - Fallback for local development only
5. **Code Updates** - Automatic fallback handling

---

## Setup Instructions

### For Local Development

#### Step 1: Create Streamlit Secrets Directory
```bash
mkdir -p .streamlit
```

#### Step 2: Create Secrets File
```bash
# Copy the template file
cp secrets.toml.example .streamlit/secrets.toml
```

#### Step 3: Add Your API Key
Edit `.streamlit/secrets.toml`:
```toml
GOOGLE_API_KEY = "your-actual-google-api-key-here"
```

#### Step 4: Get Your API Key
- Visit: https://ai.google.dev/
- Click "Get API Key"
- Create a new API key
- Copy and paste into `.streamlit/secrets.toml`

#### Step 5: Verify Setup
Run the application:
```bash
streamlit run medisync_app.py
```

The app will verify that the API key is properly configured.

**⚠️ Important:** `.streamlit/secrets.toml` is automatically ignored by `.gitignore`. Never commit it!

---

### For Kaggle Notebooks

#### Step 1: Add Secret to Kaggle
1. Open your Kaggle notebook
2. Go to **Settings** → **Secrets**
3. Click **Add Secret**
4. Name: `GOOGLE_API_KEY`
5. Value: Your Google API Key
6. Save

#### Step 2: Update Code
The code automatically reads from Kaggle's environment:
```python
# This happens automatically in the app
os.getenv('GOOGLE_API_KEY')  # Kaggle provides this
```

No additional code changes needed!

---

### For GitHub / Public Repository

#### Step 1: Verify `.gitignore`
Check that these lines are in `.gitignore`:
```
.streamlit/secrets.toml
.env
.env.*
**/api_keys.py
**/secrets.py
**/credentials.py
```

#### Step 2: Do NOT Commit Secrets
Before pushing to GitHub:
```bash
# Check what would be committed
git status

# Verify no secrets files are listed
# If .streamlit/secrets.toml appears, DO NOT COMMIT
```

#### Step 3: Update Locals
Ensure local `.streamlit/secrets.toml` has placeholder values:
```toml
# For local testing only
GOOGLE_API_KEY = "your-api-key-here"
```

#### Step 4: Users Guide
Create a `API_KEY_SETUP.md` file in your repo (already provided).

---

## Code Changes Made

### 1. `config_api_keys.py` (New)
Centralized API key management with:
- Environment variable priority
- Streamlit secrets fallback
- Detailed error messages
- Validation utilities

### 2. `utils_ocr_email.py` (Updated)
Added `get_secure_api_key()` function:
- Tries environment variable first
- Falls back to Streamlit secrets
- Clear error messages if both fail

Usage:
```python
def extract_discharge_summary_from_image(image_file, google_api_key=None):
    if not google_api_key:
        google_api_key = get_secure_api_key()
    # ... rest of function
```

### 3. `medisync_app.py` (Updated)
Automatically loads API key:
```python
import os
from utils_ocr_email import get_secure_api_key

# This happens on first use
api_key = get_secure_api_key()
```

---

## Security Best Practices

### ✅ DO:
- ✅ Use environment variables in production
- ✅ Use Streamlit secrets for local development
- ✅ Use Kaggle Secrets Manager for Kaggle notebooks
- ✅ Commit `.gitignore` and `secrets.toml.example`
- ✅ Test that API key is not in committed files
- ✅ Rotate API keys periodically
- ✅ Use different keys for different environments

### ❌ DON'T:
- ❌ Never hardcode API keys in Python files
- ❌ Never commit `.streamlit/secrets.toml` to GitHub
- ❌ Never share API keys in documentation
- ❌ Never include API keys in comments
- ❌ Never send API keys via email or chat
- ❌ Never use the same key for multiple projects
- ❌ Never log or print API keys

---

## Verification Checklist

Before submitting to GitHub or Kaggle:

- [ ] `.gitignore` exists and includes `.streamlit/secrets.toml`
- [ ] `.streamlit/secrets.toml` is NOT tracked in git
- [ ] `secrets.toml.example` exists with placeholder values
- [ ] All Python files have NO hardcoded API keys
- [ ] `config_api_keys.py` is present
- [ ] `utils_ocr_email.py` has `get_secure_api_key()` function
- [ ] Local `.streamlit/secrets.toml` has real API key for testing
- [ ] Run `git status` and verify no secrets files are staged
- [ ] Test app works with environment variable: `export GOOGLE_API_KEY="your-key"`
- [ ] Test app works with Streamlit secrets (local only)

---

## Troubleshooting

### Error: "Google API key not found"

**Solution:** Set your API key using one of these methods:

```bash
# Method 1: Environment Variable (Recommended)
export GOOGLE_API_KEY="your-api-key"

# Method 2: Streamlit Secrets (Local Development)
# Create .streamlit/secrets.toml with: GOOGLE_API_KEY = "your-api-key"

# Method 3: Python Code
import os
os.environ['GOOGLE_API_KEY'] = 'your-api-key'
```

### Error: "Could not read from Streamlit secrets"

**Solution:** Ensure `.streamlit/secrets.toml` exists and has correct format:

```toml
GOOGLE_API_KEY = "your-actual-key-here"
```

Not valid:
```toml
GOOGLE_API_KEY="your-key"  # Missing space after =
GOOGLE_API_KEY: "your-key"  # Wrong separator (should be =)
```

### My secrets are committed to GitHub!

**Immediate Actions:**

1. Rotate the API key immediately (get a new one)
2. Remove the key from git history:
   ```bash
   # Option 1: Rewrite history (if you haven't pushed yet)
   git filter-branch --tree-filter 'rm -f .streamlit/secrets.toml' HEAD
   
   # Option 2: Use GitHub's secret scanning (https://github.com/settings/security)
   # Upload the old key to mark it as revoked
   ```
3. Add `.streamlit/secrets.toml` to `.gitignore`
4. Push corrected version

---

## Environment Variable Setup for Different Platforms

### Linux / macOS (Bash/Zsh)

```bash
# Temporary (current session only)
export GOOGLE_API_KEY="your-api-key"

# Permanent (add to ~/.bashrc or ~/.zshrc)
echo 'export GOOGLE_API_KEY="your-api-key"' >> ~/.bashrc
source ~/.bashrc
```

### Windows (PowerShell)

```powershell
# Temporary (current session only)
$env:GOOGLE_API_KEY = "your-api-key"

# Permanent (System Environment Variables)
[Environment]::SetEnvironmentVariable("GOOGLE_API_KEY", "your-api-key", "User")

# Verify
$env:GOOGLE_API_KEY
```

### Windows (Command Prompt)

```cmd
# Temporary (current session only)
set GOOGLE_API_KEY=your-api-key

# Permanent (System Environment Variables)
setx GOOGLE_API_KEY "your-api-key"
```

### Kaggle Notebooks

```python
# No setup needed!
# Kaggle automatically provides environment variables

import os
api_key = os.getenv('GOOGLE_API_KEY')
```

---

## File Structure

```
Medicare Assistant/
├── .gitignore                      ✅ Prevents secrets commit
├── secrets.toml.example            ✅ Template for users
├── .streamlit/
│   └── secrets.toml                ❌ NOT COMMITTED (local only)
├── config_api_keys.py              ✅ Secure API key manager
├── utils_ocr_email.py              ✅ Updated with get_secure_api_key()
├── medisync_app.py                 ✅ Updated to use secure method
└── API_KEY_SETUP.md               ✅ This file
```

---

## Summary

| Environment | Setup Method | File | Notes |
|---|---|---|---|
| **Local Dev** | Streamlit Secrets | `.streamlit/secrets.toml` | Not committed to git |
| **Kaggle** | Environment Variable | Kaggle Secrets Manager | Automatic |
| **Production** | Environment Variable | System Env Vars | CI/CD or deployment config |
| **GitHub** | Not Needed | Reference docs | Users set up per above |

---

## Questions?

- Google API Documentation: https://ai.google.dev/docs
- Streamlit Secrets: https://docs.streamlit.io/develop/concepts/connections/secrets-management
- Kaggle Secrets: https://www.kaggle.com/docs/notebooks/setup
- Environment Variables: https://12factor.net/config

---

**Last Updated:** 2024
**Status:** ✅ Production Ready for Public Submission
