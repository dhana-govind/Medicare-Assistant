# 🏥 MediSync - Multi-Agent Healthcare Assistant

## Overview

**MediSync** is an innovative, client-side multi-agent system designed to address the critical problem of hospital readmissions by helping patients understand discharge summaries, reconcile medications, and manage follow-up appointments.

### Problem Statement
Patients often struggle to:
- Understand complex discharge summaries
- Reconcile new prescriptions with existing medications
- Identify dangerous drug interactions
- Manage follow-up appointments
- Navigate post-discharge recovery

This leads to **high hospital readmission rates** and poor patient outcomes.

### Solution Architecture

MediSync implements a **three-agent orchestration system** running on the client-side:

```
Medical Document/Discharge Summary
           ↓
┌─────────────────────────────────────────────┐
│ Agent A: The Analyzer (Vision Agent) 🔍      │
│ • Parses medical documents into JSON        │
│ • Extracts: diagnoses, medications, follow-ups
│ • Validates data quality                     │
└─────────────────────────────────────────────┘
           ↓
┌─────────────────────────────────────────────┐
│ Agent B: The Pharmacist (Logic Agent) 💊    │
│ • Cross-references medications              │
│ • Identifies dangerous interactions         │
│ • Provides clinical recommendations         │
└─────────────────────────────────────────────┘
           ↓
┌─────────────────────────────────────────────┐
│ Agent C: Care Coordinator (Chat Agent) 💙   │
│ • Maintains session state                   │
│ • Provides empathetic patient guidance      │
│ • Answers recovery questions                │
│ • Tracks engagement & compliance            │
└─────────────────────────────────────────────┘
           ↓
    Patient Knowledge Graph
    (Shared State Management)
```

## Technical Architecture

### Core Components

#### 1. **Patient Knowledge Graph** (`patient_knowledge_graph.py`)
- Centralized state management system
- Data models for:
  - Discharge summaries
  - Medications and interactions
  - Follow-up tasks
  - Agent analyses
  - Activity logs
  - Conversation history

#### 2. **Agent A: Analyzer** (`agent_analyzer.py`)
**Capabilities:**
- Vision-like document parsing (simulated with CSV processing)
- Structured data extraction
- Medication parsing
- Follow-up appointment identification
- Data quality scoring

**Outputs:**
- Structured patient discharge data
- Normalized medication list
- Extracted follow-up information

#### 3. **Agent B: Pharmacist** (`agent_pharmacist.py`)
**Capabilities:**
- Comprehensive drug-drug interaction database
- Fuzzy matching for drug name variations
- Multi-severity interaction classification
- Clinical reasoning and recommendations
- Risk stratification

**Knowledge Base Includes:**
- Anticoagulant interactions (warfarin, apixaban, etc.)
- Cardiovascular medications
- Statin interactions
- Diabetic medications
- NSAIDs, antibiotics, psychiatric drugs
- And more...

**Severity Levels:**
- 🔴 CRITICAL - Immediate intervention needed
- 🟡 MAJOR - Close monitoring required
- 🟢 MODERATE - Patient education needed
- ⚪ MINOR - Monitor for symptoms

#### 4. **Agent C: Care Coordinator** (`agent_care_coordinator.py`)
**Capabilities:**
- Patient-friendly responses
- Personalized greeting based on discharge data
- Concern classification
- Multi-topic guidance:
  - Medication management
  - Appointment scheduling
  - Symptom assessment
  - Diet & nutrition
  - Activity restrictions
  - Recovery timeline
  - Side effect management

**Session Features:**
- Conversation history tracking
- Context awareness
- Resource recommendations
- Empathetic communication

#### 5. **Main Application** (`medisync_app.py`)
Streamlit-based web interface with:
- Multi-page dashboard
- Real-time agent activity monitoring
- Data visualization with Plotly
- Patient data management
- Multi-agent orchestration UI

## Installation & Setup

### Prerequisites
- Python 3.8+
- pip (Python package manager)

### Step 1: Clone/Download Repository
```bash
cd "Medicare Assistant"
```

### Step 2: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 3: Prepare Data
Ensure you have `discharge_summaries.csv` in the directory with columns:
- `patient_id`
- `name`
- `age`
- `admission_date`
- `discharge_date`
- `primary_diagnosis`
- `secondary_diagnoses`
- `hospital_course`
- `medications`
- `follow_up`

## Quick Start

### Run the Application
```bash
streamlit run medisync_app.py
```

The application will open in your browser at `http://localhost:8501`

### Using the Dashboard

#### 1. **Load Patient Data**
   - Go to "Upload Patient" tab
   - Choose from:
     - Upload CSV file
     - Load sample/mock data
     - Manual entry

#### 2. **View Dashboard**
   - See patient overview
   - Review medications
   - Check critical alerts
   - View interaction analysis

#### 3. **Run Agent Pipeline**
   - Click "Agent Orchestration"
   - Execute "Run Full Pipeline"
   - Watch agents process patient data in real-time

#### 4. **Chat with Care Coordinator**
   - Go to "Care Coordinator Chat"
   - Ask questions about recovery
   - Get personalized guidance

#### 5. **Review Medications**
   - Check drug interactions
   - View medication details
   - See interaction recommendations

#### 6. **Export Reports**
   - Generate summary reports
   - Export as JSON/CSV
   - Download medication lists

## Feature Highlights

### 🎯 Multi-Agent Orchestration
- Sequential pipeline execution
- State sharing between agents
- Real-time activity logging
- Comprehensive audit trail

### 📊 Data Visualization
- Drug interaction severity charts
- Medication timeline displays
- Patient health metrics
- Activity log monitoring

### 🛡️ Safety Features
- Comprehensive drug interaction database
- Critical alert system
- Emergency symptom detection
- Clinical recommendation engine

### 💻 User Experience
- Responsive Streamlit interface
- Multi-page navigation
- Real-time processing indicators
- Downloadable reports
- Export to JSON/CSV

## Sample Use Case

### Patient: John Smith (P001)
**Diagnosis:** Acute Myocardial Infarction (STEMI)

**Process:**
1. **Analyzer** extracts:
   - Primary diagnosis: AMI
   - Medications: 6 medications
   - Follow-ups: Cardiology + PCP

2. **Pharmacist** identifies:
   - ⚠️ MAJOR: Aspirin + Clopidogrel (dual antiplatelet)
   - ⚠️ MODERATE: NSAIDs + Lisinopril interaction risk
   - ✅ Recommendations provided

3. **Care Coordinator** helps with:
   - Understanding medications
   - Activity restrictions (no lifting 4 weeks)
   - Appointment scheduling
   - Recovery timeline (8-12 weeks)
   - Warning signs (chest pain, SOB)

## Project Structure

```
Medicare Assistant/
├── medisync_app.py                 # Main Streamlit application
├── patient_knowledge_graph.py      # State management & data models
├── agent_analyzer.py               # Vision/Document parsing agent
├── agent_pharmacist.py             # Drug interaction analysis agent
├── agent_care_coordinator.py       # Patient chat & guidance agent
├── discharge_summaries.csv         # Sample patient data
├── requirements.txt                # Python dependencies
└── README.md                       # This file
```

## Key Innovations

### 1. **Client-Side Multi-Agent System**
- All processing happens locally
- No dependency on external APIs (except for potential future enhancements)
- Privacy-preserving architecture

### 2. **State Management via Knowledge Graph**
- Centralized patient data structure
- Enables seamless agent collaboration
- Real-time synchronization

### 3. **Comprehensive Drug Interaction Database**
- 30+ documented interactions
- Multi-severity classification
- Clinical recommendations

### 4. **Empathetic AI Design**
- Patient-friendly language
- Personalized responses
- Emotional support integration

### 5. **Real-Time Observability**
- Agent Activity Log visualization
- Reasoning transparency
- Audit trail for compliance

## Use Cases

### 1. **Post-Discharge Patient Support**
- Automate patient education
- Reduce readmission rates
- Improve medication adherence

### 2. **Pharmacy Services**
- Detect medication interactions
- Support clinical decision-making
- Patient counseling resource

### 3. **Care Coordination**
- Track patient engagement
- Manage follow-ups
- Identify high-risk patients

### 4. **Healthcare Training**
- Educational tool for students
- Clinical reasoning examples
- Safety awareness

## Future Enhancements

- [ ] Vision API integration for document scanning
- [ ] Google Search grounding for real-time drug information
- [ ] Advanced NLP for patient question understanding
- [ ] Integration with EHR systems
- [ ] Mobile app deployment
- [ ] Predictive readmission risk scoring
- [ ] Multi-language support
- [ ] Compliance reporting (HIPAA, HL7)

## Testing & Validation

### Run with Sample Data
```bash
streamlit run medisync_app.py
# Go to "Upload Patient" → "Sample Data" → Load Mock Patient
```

### Test Agent Pipeline
```bash
# In "Agent Orchestration" tab
# Click "Run Full Pipeline" to see all agents in action
```

## Limitations & Disclaimers

⚠️ **Important:**
- This is a **demonstration system** for educational purposes
- Should NOT replace professional medical judgment
- Drug interaction database is simplified (not comprehensive)
- Always consult healthcare providers for medical decisions
- Not suitable for emergency situations (call 911)

## Performance Metrics

- **Agent Processing Time:** < 5 seconds per patient
- **Drug Interactions Checked:** Scales with medication count (O(n²))
- **Memory Usage:** ~10-50MB per patient session
- **UI Responsiveness:** Real-time updates

## Kaggle Capstone Submission

This project demonstrates:
- ✅ Multi-agent system architecture
- ✅ Healthcare domain expertise
- ✅ Data management & visualization
- ✅ Clinical decision support
- ✅ User experience design
- ✅ Code modularity & reusability

## Contributing

To extend MediSync:

1. Add more drug interactions to `agent_pharmacist.py`
2. Enhance response templates in `agent_care_coordinator.py`
3. Add new visualization types in `medisync_app.py`
4. Implement real API integrations

## License

This project is provided as-is for educational and research purposes.

## Support & Questions

For issues, questions, or feature requests, please refer to the project documentation or review the source code comments.

---

**Built with ❤️ for better patient outcomes**

*MediSync: Where AI meets Empathy in Healthcare*
