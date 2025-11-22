# MediSync Setup Guide - New Features (5-Minute Quick Start)

## ⚡ Quick Setup

### Step 1: Google API Key for Image OCR (2 minutes)
```
1. Go to https://ai.google.dev/
2. Click "Get API Key"
3. Create new project if needed
4. Copy the API key
5. Done! You'll paste this into the app
```

### Step 2: Gmail Setup for Email Reminders (2 minutes)

**Enable 2-Factor Authentication:**
```
1. Visit https://myaccount.google.com/security
2. Look for "2-Step Verification"
3. Click "Enable"
4. Follow Google's instructions
5. Done!
```

**Create App Password:**
```
1. Go to https://myaccount.google.com/apppasswords
2. Select "Mail" and "Windows Computer"
3. Click "Generate"
4. You'll get a 16-character password
5. Copy it (IMPORTANT: This is NOT your Gmail password!)
6. Done!
```

### Step 3: Configure MediSync (1 minute)

**Create `.streamlit/secrets.toml` in your project folder:**

```toml
# Email Settings
SENDER_EMAIL = "your-gmail@gmail.com"
SENDER_PASSWORD = "xxxx xxxx xxxx xxxx"  # 16-char app password

# Google API Key (optional - can enter in UI)
GOOGLE_API_KEY = "your-google-api-key"
```

**Or use without secrets.toml:**
- Just enter Google API Key in the app UI
- Enter email sender credentials before sending reminders

---

## 🎯 How to Use Each Feature

### Feature 1: Dropdown Patient Selector
**Location**: Upload Patient → From CSV

```
1. Upload CSV file
2. Click dropdown ▼
3. Select patient
4. Click "Load Selected Patient"
```

### Feature 2: Image-Based Patient Upload
**Location**: Upload Patient → From Image (OCR)

```
1. Paste Google API Key (or use from secrets)
2. Click "Upload discharge summary image"
3. Choose image file (JPG/PNG)
4. Click "Extract Data from Image"
5. Review extracted data
6. Click "Load Extracted Patient Data"
```

### Feature 3: Send Appointment Reminder Email
**Location**: Medication Review (scroll to bottom)

```
1. Select follow-up appointment
2. Enter patient email
3. Enter provider name
4. Enter appointment date
5. Click "Send Reminder Email"
6. ✅ Email sent!
```

---

## 📱 What Gets Extracted from Images

When you upload a discharge summary image, the system automatically extracts:

```
✅ Patient Name
✅ Patient ID / MRN
✅ Age & Gender
✅ Admission & Discharge Dates
✅ Primary Diagnosis
✅ Secondary Diagnoses
✅ Current Medications (with dosage)
✅ Allergies
✅ Follow-up Appointments
✅ Contact Email & Phone
```

---

## 🚀 Test Everything

### Test Image OCR:
1. Take a photo of a discharge summary
2. Upload to "From Image (OCR)"
3. Verify extracted data matches the document

### Test Email Sending:
1. Load a patient with follow-up
2. Go to Medication Review
3. Send test reminder to your own email
4. Check email arrived correctly

### Test Dropdown:
1. Upload multi-patient CSV
2. Use dropdown to switch between patients
3. Verify only one patient's data shows at a time

---

## ✅ Pre-Deployment Checklist

- [ ] Google API Key obtained
- [ ] Gmail 2FA enabled
- [ ] App-specific password created
- [ ] `.streamlit/secrets.toml` created (optional)
- [ ] Image OCR tested with real document
- [ ] Email reminder tested and received
- [ ] Dropdown patient switching tested
- [ ] No data consolidation between patients
- [ ] All agents working without errors

---

## 🆘 Common Issues & Fixes

| Issue | Solution |
|-------|----------|
| "Invalid API key" | Check key at https://ai.google.dev/ |
| "Authentication failed (email)" | Use 16-char app password, not Gmail password |
| "Image text not extracted" | Use clearer, well-lit image |
| "Dropdown won't populate" | Make sure CSV has name/patient_id columns |
| "Email not sent" | Verify 2FA is enabled on Gmail |
| "Module not found" | Run `pip install google-generativeai` |

---

## 📧 Email Format Example

When patient receives reminder:

```
Subject: 📅 Appointment Reminder - Cardiology with Dr. Smith

Dear John Smith,

This is a reminder about your upcoming appointment.

APPOINTMENT DETAILS:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📅 Date & Time: December 15, 2024 at 2:00 PM
👨‍⚕️ Provider: Dr. Smith
🏥 Specialty: Cardiology

IMPORTANT:
• Please arrive 10-15 minutes early
• Bring your insurance card and photo ID
• Bring a list of current medications
• Wear comfortable clothing

If you need to reschedule or cancel, please contact 
our office at least 24 hours in advance.

Best regards,
MediSync Healthcare Assistant
🏥 Your Personal Healthcare Coordinator
```

---

## 🔐 Security Notes

⚠️ **NEVER commit `.streamlit/secrets.toml` to Git!**

Add to `.gitignore`:
```
.streamlit/secrets.toml
```

For team projects:
- Share `secrets.toml.example` (without actual values)
- Each team member creates their own `secrets.toml`
- Use environment variables for production

---

## 📱 Access Points

```
Local: http://localhost:8501
Network: http://192.168.1.249:8501
```

---

## ❓ Need Help?

1. Check FEATURE_ENHANCEMENTS.md for detailed docs
2. Review error message in app
3. Check terminal for logs
4. Try clearing Streamlit cache: `streamlit cache clear`
5. Restart app

---

**All set! Your MediSync app is ready with three powerful new features!** 🎉
