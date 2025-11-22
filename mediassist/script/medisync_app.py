"""
MediSync - Multi-Agent Healthcare Assistant
Main Streamlit Application
Orchestrates three specialized agents for comprehensive patient care coordination
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import json
from io import StringIO
import os

# Import custom modules
from patient_knowledge_graph import PatientKnowledgeGraph, InteractionSeverity
from agent_analyzer import AnalyzerAgent, create_mock_discharge_data
from agent_pharmacist import PharmacistAgent
from agent_care_coordinator import CareCoordinatorAgent
from utils_ocr_email import extract_discharge_summary_from_image
from mcp_server import get_mcp_server, ToolType, ToolDefinition, Parameter, ParameterType
from a2a_protocol import get_a2a_protocol


# ============================================================================
# STREAMLIT PAGE CONFIGURATION
# ============================================================================

st.set_page_config(
    page_title="MediSync - Medical Assistant",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS styling
st.markdown("""
    <style>
    .main {
        padding-top: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        margin: 10px 0;
    }
    .alert-critical {
        background-color: #ffcccc;
        border-left: 4px solid #ff0000;
        padding: 10px;
        border-radius: 5px;
    }
    .alert-major {
        background-color: #fff3cd;
        border-left: 4px solid #ffc107;
        padding: 10px;
        border-radius: 5px;
    }
    .alert-success {
        background-color: #d4edda;
        border-left: 4px solid #28a745;
        padding: 10px;
        border-radius: 5px;
    }
    .agent-card {
        border: 2px solid #667eea;
        border-radius: 10px;
        padding: 15px;
        margin: 10px 0;
        background-color: #f8f9ff;
    }
    </style>
""", unsafe_allow_html=True)


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def load_sample_data():
    """Load sample discharge summary data from CSV"""
    try:
        df = pd.read_csv("discharge_summaries.csv")
        return df.to_dict(orient="records")
    except FileNotFoundError:
        st.warning("discharge_summaries.csv not found. Using mock data.")
        return [create_mock_discharge_data()]


def _register_mcp_tools(mcp_server):
    """Register all available tools with the MCP Server"""
    
    # Tool 1: Extract Patient Data
    def extract_patient_tool(patient_data: dict) -> dict:
        """Extract and structure patient data"""
        return {"status": "extracted", "patient_id": patient_data.get("patient_id")}
    
    tool1 = ToolDefinition(
        name="extract_patient_data",
        description="Extract and structure patient discharge summary data",
        tool_type=ToolType.CUSTOM,
        handler=extract_patient_tool,
        parameters=[
            Parameter(
                name="patient_data",
                type=ParameterType.OBJECT,
                description="Patient data dictionary",
                required=True
            )
        ],
        tags=["extraction", "patient-data"]
    )
    mcp_server.register_tool(tool1, aliases=["extract_data", "parse_patient"])
    
    # Tool 2: Analyze Medications
    def analyze_medications_tool(medications: list) -> dict:
        """Analyze medication interactions"""
        return {"medications_analyzed": len(medications), "status": "completed"}
    
    tool2 = ToolDefinition(
        name="analyze_medications",
        description="Analyze medications for potential interactions",
        tool_type=ToolType.CUSTOM,
        handler=analyze_medications_tool,
        parameters=[
            Parameter(
                name="medications",
                type=ParameterType.ARRAY,
                description="List of medications",
                required=True
            )
        ],
        tags=["medication", "interaction-analysis"]
    )
    mcp_server.register_tool(tool2, aliases=["check_interactions", "med_analysis"])
    
    # Tool 3: Generate Patient Report
    def generate_report_tool(patient_id: str, report_type: str = "summary") -> dict:
        """Generate comprehensive patient report"""
        return {
            "patient_id": patient_id,
            "report_type": report_type,
            "generated": True,
            "timestamp": datetime.now().isoformat()
        }
    
    tool3 = ToolDefinition(
        name="generate_report",
        description="Generate comprehensive patient report",
        tool_type=ToolType.CUSTOM,
        handler=generate_report_tool,
        parameters=[
            Parameter(
                name="patient_id",
                type=ParameterType.STRING,
                description="Patient identifier",
                required=True
            ),
            Parameter(
                name="report_type",
                type=ParameterType.STRING,
                description="Type of report (summary, detailed, medication)",
                required=False,
                default="summary"
            )
        ],
        tags=["reporting", "export"]
    )
    mcp_server.register_tool(tool3, aliases=["create_report", "export_data"])


# ============================================================================
# SESSION STATE INITIALIZATION (After function definitions)
# ============================================================================

if "knowledge_graph" not in st.session_state:
    st.session_state.knowledge_graph = PatientKnowledgeGraph()

if "analyzer_agent" not in st.session_state:
    st.session_state.analyzer_agent = AnalyzerAgent(st.session_state.knowledge_graph)

if "pharmacist_agent" not in st.session_state:
    st.session_state.pharmacist_agent = PharmacistAgent(st.session_state.knowledge_graph)

if "care_coordinator_agent" not in st.session_state:
    st.session_state.care_coordinator_agent = CareCoordinatorAgent(st.session_state.knowledge_graph)

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "processing_stage" not in st.session_state:
    st.session_state.processing_stage = "initial"

if "pending_patient_data" not in st.session_state:
    st.session_state.pending_patient_data = None

if "last_extracted_data" not in st.session_state:
    st.session_state.last_extracted_data = None

# Initialize MCP Server and A2A Protocol
if "mcp_server" not in st.session_state:
    st.session_state.mcp_server = get_mcp_server()
    _register_mcp_tools(st.session_state.mcp_server)

if "a2a_protocol" not in st.session_state:
    st.session_state.a2a_protocol = get_a2a_protocol()


def normalize_ocr_data(ocr_data: dict) -> dict:
    """Convert OCR extracted data to format expected by analyzer"""
    # Convert medications list to comma-separated string
    medications_str = ""
    if ocr_data.get("medications"):
        meds = ocr_data["medications"]
        if isinstance(meds, list):
            med_strs = []
            for med in meds:
                if isinstance(med, dict):
                    # Format: "Drug Name Dosage Frequency"
                    parts = [
                        med.get("name", ""),
                        med.get("dosage", ""),
                        med.get("frequency", "")
                    ]
                    med_strs.append(" ".join([p for p in parts if p]))
                else:
                    med_strs.append(str(med))
            medications_str = ", ".join(med_strs)
        else:
            medications_str = str(meds)
    
    # Convert follow_ups list to string
    followup_str = ""
    if ocr_data.get("follow_up"):
        followups = ocr_data["follow_up"]
        if isinstance(followups, list):
            followup_strs = []
            for fu in followups:
                if isinstance(fu, dict):
                    parts = [
                        fu.get("specialty", ""),
                        fu.get("description", ""),
                        fu.get("days", "")
                    ]
                    followup_strs.append(" ".join([p for p in parts if p]))
                else:
                    followup_strs.append(str(fu))
            followup_str = ", ".join(followup_strs)
        else:
            followup_str = str(followups)
    
    # Normalize the data
    normalized = {
        "patient_id": ocr_data.get("patient_id", "UNKNOWN"),
        "name": ocr_data.get("patient_name", ""),
        "age": ocr_data.get("age"),
        "sex": ocr_data.get("sex", ""),
        "admission_date": ocr_data.get("admission_date", ""),
        "discharge_date": ocr_data.get("discharge_date", ""),
        "primary_diagnosis": ocr_data.get("primary_diagnosis", ""),
        "secondary_diagnoses": ocr_data.get("secondary_diagnoses", []),
        "hospital_course": ocr_data.get("hospital_course", ""),
        "discharge_instructions": ocr_data.get("discharge_instructions", ""),
        "medications": medications_str,
        "follow_up": followup_str,
        "allergies": ocr_data.get("allergies", []),
        "precautions": ocr_data.get("precautions", [])
    }
    
    return normalized


def run_analyzer_agent(patient_data):
    """Execute Analyzer Agent on discharge data"""
    # Normalize OCR data if it has raw_text field
    if "raw_text" in patient_data:
        patient_data = normalize_ocr_data(patient_data)
    
    with st.spinner("🔍 Analyzer: Processing medical documents..."):
        analysis = st.session_state.analyzer_agent.analyze_discharge_summary(patient_data)
        return analysis


def run_pharmacist_agent():
    """Execute Pharmacist Agent for medication interaction analysis"""
    with st.spinner("💊 Pharmacist: Checking medication interactions..."):
        analysis = st.session_state.pharmacist_agent.check_medication_interactions()
        return analysis


def display_agent_analysis(analysis, agent_name):
    """Display agent analysis results"""
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col1:
        status_color = "🟢" if analysis.status == "completed" else "🔴" if analysis.status == "error" else "🟡"
        st.metric(f"{status_color} Status", analysis.status.upper())
    
    with col2:
        st.metric("Execution Time", f"{analysis.execution_time_seconds:.2f}s")
    
    with col3:
        st.metric("Timestamp", analysis.timestamp.split("T")[1][:8])
    
    if analysis.findings:
        with st.expander("📊 Findings"):
            st.json(analysis.findings)
    
    if analysis.reasoning:
        with st.expander("🧠 Reasoning"):
            st.text(analysis.reasoning)
    
    if analysis.recommendations:
        with st.expander("✅ Recommendations"):
            for i, rec in enumerate(analysis.recommendations, 1):
                st.write(f"{i}. {rec}")


def display_critical_alerts():
    """Display critical alerts from pharmacist"""
    kg = st.session_state.knowledge_graph
    critical = kg.get_critical_interactions()
    
    if critical:
        st.markdown('<div class="alert-critical">', unsafe_allow_html=True)
        st.error(f"🚨 **CRITICAL: {len(critical)} Medication Interaction(s) Detected**")
        for interaction in critical:
            st.write(f"**{interaction.drug1} + {interaction.drug2}**")
            st.write(f"⚠️ {interaction.description}")
            st.write(f"✅ Recommendation: {interaction.recommendation}")
            st.divider()
        st.markdown('</div>', unsafe_allow_html=True)


def visualize_interaction_summary():
    """Create visualization of drug interactions"""
    kg = st.session_state.knowledge_graph
    interactions = kg.drug_interactions
    
    if not interactions:
        st.info("No drug interactions detected. ✅")
        return
    
    # Count by severity
    severity_counts = {}
    for severity in InteractionSeverity:
        severity_counts[severity.value] = len(kg.get_interactions_by_severity(severity))
    
    severity_counts = {k: v for k, v in severity_counts.items() if v > 0}
    
    if severity_counts:
        # Create bar chart
        fig = px.bar(
            x=list(severity_counts.keys()),
            y=list(severity_counts.values()),
            title="Drug Interactions by Severity",
            labels={"x": "Severity Level", "y": "Count"},
            color=list(severity_counts.keys()),
            color_discrete_map={
                "critical": "#ff0000",
                "major": "#ffc107",
                "moderate": "#17a2b8",
                "minor": "#28a745",
                "none": "#6c757d"
            }
        )
        st.plotly_chart(fig, use_container_width=True)


def visualize_medication_timeline():
    """Create medication timeline visualization"""
    kg = st.session_state.knowledge_graph
    medications = kg.get_current_medications()
    
    if not medications:
        st.info("No medications to display.")
        return
    
    # Create medication list with visual representation
    fig = go.Figure()
    
    for i, med in enumerate(medications):
        fig.add_trace(go.Bar(
            name=med.name,
            x=[med.frequency],
            y=[i],
            orientation='h',
            text=f"{med.name} {med.dosage}",
            textposition="auto",
        ))
    
    fig.update_layout(
        title="Current Medications",
        showlegend=False,
        height=300,
        xaxis_title="Frequency",
        yaxis_ticktext=[med.name for med in medications],
        yaxis_tickvals=list(range(len(medications)))
    )
    
    st.plotly_chart(fig, use_container_width=True)


def display_activity_log():
    """Display real-time activity log"""
    kg = st.session_state.knowledge_graph
    activities = kg.get_activity_log(limit=20)
    
    if not activities:
        st.info("No activities yet.")
        return
    
    # Create DataFrame for better display
    df = pd.DataFrame(activities)
    df['timestamp'] = pd.to_datetime(df['timestamp']).dt.strftime("%H:%M:%S")
    
    # Color code by level
    level_colors = {
        "info": "ℹ️",
        "warning": "⚠️",
        "error": "❌",
        "success": "✅"
    }
    
    for _, row in df.iterrows():
        icon = level_colors.get(row['level'], "•")
        st.write(f"{icon} **[{row['source'].upper()}]** {row['timestamp']}: {row['message']}")


# ============================================================================
# MAIN APPLICATION LAYOUT
# ============================================================================

def main():
    # Header
    col1, col2, col3 = st.columns([1, 2, 1])
    with col1:
        st.image("https://img.icons8.com/color/96/000000/hospital-2.png", width=80)
    with col2:
        st.title("🏥 MediSync")
        st.markdown("### Multi-Agent Healthcare Assistant")
        st.markdown("*Intelligent coordination between Analyzer, Pharmacist, and Care Coordinator agents*")
    with col3:
        st.metric("System Status", "🟢 ACTIVE")
    
    st.divider()
    
    # Sidebar Navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.radio(
        "Select Module:",
        ["Dashboard", "Upload Patient", "Agent Orchestration", "Care Coordinator Chat", 
         "Medication Review", "Reports & Export"],
        key="nav_page"
    )
    
    # Process pending patient data if it exists (after all functions are defined)
    if st.session_state.pending_patient_data is not None:
        with st.spinner("📂 Loading patient data into knowledge graph..."):
            patient_data = st.session_state.pending_patient_data
            # Run analyzer to populate knowledge graph
            analysis = run_analyzer_agent(patient_data)
            st.session_state.last_analysis = analysis
        # Clear pending data after processing
        st.session_state.pending_patient_data = None
        st.success("✅ Patient data loaded successfully!")
        st.info(f"Processed: {analysis.findings.get('patient_name', 'Unknown')}")
    
    st.sidebar.divider()
    st.sidebar.markdown("### System Status")
    
    kg = st.session_state.knowledge_graph
    if kg.discharge_summary:
        st.sidebar.success(f"✅ Patient Loaded: {kg.discharge_summary.patient_name}")
    else:
        st.sidebar.warning("⚠️ No patient data loaded")
    
    st.sidebar.metric("Current Medications", len(kg.get_current_medications()))
    st.sidebar.metric("Drug Interactions", len(kg.drug_interactions))
    st.sidebar.metric("Follow-ups", len(kg.get_pending_follow_ups()))
    
    # ========== PAGE: DASHBOARD ==========
    if page == "Dashboard":
        st.header("📊 Patient Dashboard")
        
        if kg.discharge_summary:
            # Patient Overview
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Patient", kg.discharge_summary.patient_name)
            with col2:
                st.metric("Patient ID", kg.discharge_summary.patient_id)
            with col3:
                st.metric("Diagnosis", kg.discharge_summary.primary_diagnosis[:30])
            with col4:
                st.metric("Discharge Date", kg.discharge_summary.discharge_date)
            
            st.divider()
            
            # Critical Alerts
            display_critical_alerts()
            
            st.divider()
            
            # Health Metrics Row
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("💊 Medication Overview")
                meds = kg.get_current_medications()
                st.metric("Total Medications", len(meds))
                if meds:
                    for med in meds[:5]:
                        st.write(f"• {med.name} {med.dosage} ({med.frequency})")
                    if len(meds) > 5:
                        st.caption(f"... and {len(meds) - 5} more")
            
            with col2:
                st.subheader("📅 Follow-up Schedule")
                follow_ups = kg.get_pending_follow_ups()
                st.metric("Pending Follow-ups", len(follow_ups))
                if follow_ups:
                    for task in follow_ups[:3]:
                        st.write(f"• {task.specialty}: {task.description}")
            
            st.divider()
            
            # Visualizations
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("Interaction Risk Levels")
                visualize_interaction_summary()
            
            with col2:
                st.subheader("Medication List")
                visualize_medication_timeline()
            
            st.divider()
            
            # Activity Log
            st.subheader("📝 Agent Activity Log")
            display_activity_log()
        
        else:
            st.info("👈 Load a patient from the sidebar to view dashboard")
    
    # ========== PAGE: UPLOAD PATIENT ==========
    elif page == "Upload Patient":
        st.header("📤 Load Patient Data")
        
        tab1, tab2, tab3 = st.tabs(["From CSV", "From Image (OCR)", "Manual Entry"])
        
        with tab1:
            st.subheader("Upload Discharge Summary CSV")
            uploaded_file = st.file_uploader("Choose CSV file", type="csv", key="csv_uploader")
            
            if uploaded_file is not None:
                df = pd.read_csv(uploaded_file)
                st.write("Preview:")
                st.dataframe(df.head())
                
                st.divider()
                st.subheader("Select Patient Record")
                
                # Create patient selector with dropdown (selectbox)
                patient_options = {}
                for idx in range(len(df)):
                    patient_name = df.iloc[idx].get('name', df.iloc[idx].get('patient_name', f'Patient {idx+1}'))
                    patient_id = df.iloc[idx].get('patient_id', df.iloc[idx].get('id', f'P{idx+1:03d}'))
                    display_label = f"{patient_name} (ID: {patient_id})"
                    patient_options[display_label] = idx
                
                # Dropdown selector
                selected_patient = st.selectbox(
                    "Choose a patient to load:",
                    options=list(patient_options.keys()),
                    key="patient_selectbox"
                )
                
                if st.button("Load Selected Patient", type="primary", use_container_width=True):
                    record_index = patient_options[selected_patient]
                    
                    # Reset session state for new patient
                    st.session_state.knowledge_graph = PatientKnowledgeGraph()
                    st.session_state.analyzer_agent = AnalyzerAgent(st.session_state.knowledge_graph)
                    st.session_state.pharmacist_agent = PharmacistAgent(st.session_state.knowledge_graph)
                    st.session_state.care_coordinator_agent = CareCoordinatorAgent(st.session_state.knowledge_graph)
                    st.session_state.chat_history = []
                    st.session_state.processing_stage = "initial"
                    
                    patient_data = df.iloc[record_index].to_dict()
                    with st.spinner("Loading patient data..."):
                        analysis = run_analyzer_agent(patient_data)
                        st.success("✅ Patient data loaded successfully!")
                        st.info(f"Processed: {analysis.findings.get('patient_name', 'Unknown')}")
                        st.rerun()
        
        with tab2:
            st.subheader("📸 Upload Discharge Summary Image")
            st.info("📖 Supported formats: JPG, PNG (extracts text using Google Gemini)")
            
            # Check if API key is configured
            google_api_key = st.secrets.get("GOOGLE_API_KEY", "")
            
            if not google_api_key:
                st.error("""
                ❌ Google API Key not configured!
                
                **Setup Instructions:**
                1. Get API key from https://ai.google.dev/
                2. Add to `.streamlit/secrets.toml`:
                   ```
                   GOOGLE_API_KEY = "your-api-key-here"
                   ```
                3. Restart the app
                """)
            else:
                st.success("✅ API Key configured")
            
            # Image uploader
            image_file = st.file_uploader(
                "Upload discharge summary image",
                type=["jpg", "jpeg", "png"],
                key="image_uploader"
            )
            
            if image_file is not None:
                # Display uploaded image
                st.image(image_file, caption="Uploaded discharge summary", use_container_width=True)
                
                st.divider()
                
                if st.button("Extract Data from Image (OCR)", type="primary", use_container_width=True):
                    if not google_api_key:
                        st.error("❌ Please configure Google API Key in secrets file")
                    else:
                        with st.spinner("🔄 Extracting text from image using Gemini Vision..."):
                            success, extracted_data = extract_discharge_summary_from_image(image_file, google_api_key)
                            
                            if success:
                                st.success("✅ Successfully extracted data from image!")
                                st.session_state.last_extracted_data = extracted_data
                                
                                # Display extracted data
                                with st.expander("📋 Extracted Information", expanded=True):
                                    st.json(extracted_data)
                            else:
                                st.error(f"❌ Failed to extract data: {extracted_data.get('error', 'Unknown error')}")
                
                # Show load button if we have extracted data
                if "last_extracted_data" in st.session_state and st.session_state.last_extracted_data:
                    st.divider()
                    if st.button("Load Extracted Patient Data", type="primary", use_container_width=True):
                        # Store extracted data in session state
                        st.session_state.pending_patient_data = st.session_state.last_extracted_data
                        
                        # Reset session state for new patient
                        st.session_state.knowledge_graph = PatientKnowledgeGraph()
                        st.session_state.analyzer_agent = AnalyzerAgent(st.session_state.knowledge_graph)
                        st.session_state.pharmacist_agent = PharmacistAgent(st.session_state.knowledge_graph)
                        st.session_state.care_coordinator_agent = CareCoordinatorAgent(st.session_state.knowledge_graph)
                        st.session_state.chat_history = []
                        st.session_state.processing_stage = "initial"
                        
                        # Store patient email if available
                        if 'contact_email' in st.session_state.last_extracted_data:
                            st.session_state.patient_email = st.session_state.last_extracted_data['contact_email']
                        
                        # Trigger rerun to process pending data
                        st.rerun()
        
        with tab3:
            st.subheader("Manual Patient Entry")
            
            col1, col2 = st.columns(2)
            with col1:
                patient_id = st.text_input("Patient ID", "P001")
                patient_name = st.text_input("Patient Name", "John Smith")
                age = st.number_input("Age", 18, 120, 45)
            
            with col2:
                admission_date = st.date_input("Admission Date", datetime.now() - timedelta(days=7))
                discharge_date = st.date_input("Discharge Date", datetime.now())
                sex = st.selectbox("Sex", ["Male", "Female", "Other"])
            
            diagnosis = st.text_area("Primary Diagnosis", "Acute Myocardial Infarction")
            medications = st.text_area("Medications (comma-separated)", "Aspirin 325mg daily, Metoprolol 50mg twice daily")
            follow_up = st.text_area("Follow-up", "Cardiology in 1 week")
            
            if st.button("Load Manual Entry", use_container_width=True, type="primary"):
                # Reset session state for new patient
                st.session_state.knowledge_graph = PatientKnowledgeGraph()
                st.session_state.analyzer_agent = AnalyzerAgent(st.session_state.knowledge_graph)
                st.session_state.pharmacist_agent = PharmacistAgent(st.session_state.knowledge_graph)
                st.session_state.care_coordinator_agent = CareCoordinatorAgent(st.session_state.knowledge_graph)
                st.session_state.chat_history = []
                st.session_state.processing_stage = "initial"
                
                patient_data = {
                    "patient_id": patient_id,
                    "name": patient_name,
                    "age": age,
                    "sex": sex,
                    "admission_date": str(admission_date),
                    "discharge_date": str(discharge_date),
                    "primary_diagnosis": diagnosis,
                    "medications": medications,
                    "follow_up": follow_up
                }
                
                with st.spinner("Loading patient data..."):
                    analysis = run_analyzer_agent(patient_data)
                    st.success("✅ Patient loaded successfully!")
                    st.rerun()
    
    # ========== PAGE: AGENT ORCHESTRATION ==========
    elif page == "Agent Orchestration":
        st.header("🤖 Multi-Agent Orchestration Pipeline")
        
        st.info("""
        This system orchestrates three specialized agents in a pipeline:
        1. **Agent A (Analyzer)**: Parses medical documents into structured data
        2. **Agent B (Pharmacist)**: Analyzes medications for dangerous interactions
        3. **Agent C (Care Coordinator)**: Provides empathetic patient guidance
        """)
        
        if not kg.discharge_summary:
            st.warning("⚠️ Please load a patient first from the 'Upload Patient' tab")
        else:
            st.subheader("📋 Current Patient")
            col1, col2, col3 = st.columns(3)
            col1.metric("Patient", kg.discharge_summary.patient_name)
            col2.metric("Diagnosis", kg.discharge_summary.primary_diagnosis)
            col3.metric("Medications", len(kg.get_current_medications()))
            
            st.divider()
            
            # Agent Pipeline Execution
            st.subheader("🔄 Execute Agent Pipeline")
            
            if st.button("Run Full Pipeline", use_container_width=True, type="primary"):
                st.session_state.processing_stage = "running"
            
            if st.session_state.processing_stage == "running":
                # Agent A: Analyzer
                st.subheader("Agent A: The Analyzer 🔍")
                latest_analyzer = kg.get_latest_agent_analysis("analyzer")
                if latest_analyzer:
                    with st.container(border=True):
                        display_agent_analysis(latest_analyzer, "Analyzer")
                
                st.divider()
                
                # Agent B: Pharmacist
                st.subheader("Agent B: The Pharmacist 💊")
                pharmacist_analysis = run_pharmacist_agent()
                with st.container(border=True):
                    display_agent_analysis(pharmacist_analysis, "Pharmacist")
                
                # Display interactions
                if kg.drug_interactions:
                    st.warning("⚠️ Drug Interactions Detected")
                    for interaction in kg.drug_interactions:
                        cols = st.columns([1, 2, 1])
                        with cols[0]:
                            severity_emoji = {"critical": "🔴", "major": "🟡", "moderate": "🟢"}.get(
                                interaction.severity.value, "⚪"
                            )
                            st.write(f"{severity_emoji} {interaction.severity.value.upper()}")
                        with cols[1]:
                            st.write(f"**{interaction.drug1} + {interaction.drug2}**")
                            st.caption(interaction.description)
                        with cols[2]:
                            st.write(f"*{interaction.recommendation}*")
                        st.divider()
                
                st.divider()
                
                # Agent C: Care Coordinator
                st.subheader("Agent C: The Care Coordinator 💙")
                greeting, cc_analysis = st.session_state.care_coordinator_agent.initiate_patient_engagement()
                with st.container(border=True):
                    display_agent_analysis(cc_analysis, "Care Coordinator")
                
                st.divider()
                st.success("✅ Pipeline execution complete!")
                st.session_state.processing_stage = "complete"
    
    # ========== PAGE: CARE COORDINATOR CHAT ==========
    elif page == "Care Coordinator Chat":
        st.header("💬 Care Coordinator Chat")
        
        if not kg.discharge_summary:
            st.warning("⚠️ Please load a patient first")
        else:
            st.write(f"Chatting with **{kg.discharge_summary.patient_name}** about their recovery")
            
            # Display chat history
            for msg in st.session_state.chat_history:
                if msg["role"] == "user":
                    st.chat_message("user").write(msg["content"])
                else:
                    st.chat_message("assistant").write(msg["content"])
            
            # Chat input
            user_input = st.chat_input("Ask me anything about your recovery...")
            
            if user_input:
                st.session_state.chat_history.append({"role": "user", "content": user_input})
                st.chat_message("user").write(user_input)
                
                with st.spinner("Care Coordinator is thinking..."):
                    response, analysis = st.session_state.care_coordinator_agent.respond_to_patient_question(user_input)
                
                st.session_state.chat_history.append({"role": "assistant", "content": response})
                st.chat_message("assistant").write(response)
                
                with st.expander("📊 Agent Analysis"):
                    st.json(analysis.findings)
    
    # ========== PAGE: MEDICATION REVIEW ==========
    elif page == "Medication Review":
        st.header("💊 Medication Review & Interactions")
        
        if not kg.discharge_summary:
            st.warning("⚠️ Please load a patient first")
        else:
            display_critical_alerts()
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Current Medications")
                medications = kg.get_current_medications()
                
                if medications:
                    df_meds = pd.DataFrame([
                        {
                            "Name": m.name,
                            "Dosage": m.dosage,
                            "Frequency": m.frequency,
                            "Route": m.route
                        }
                        for m in medications
                    ])
                    st.dataframe(df_meds, use_container_width=True)
                else:
                    st.info("No medications recorded")
            
            with col2:
                st.subheader("Allergies")
                allergies = kg.get_allergies()
                if allergies:
                    for allergy in allergies:
                        st.warning(f"🚫 {allergy}")
                else:
                    st.success("✅ No known allergies")
            
            st.divider()
            
            st.subheader("Drug Interaction Analysis")
            interactions = kg.drug_interactions
            
            if not interactions:
                st.success("✅ No drug interactions detected")
            else:
                st.warning(f"⚠️ {len(interactions)} interaction(s) found")
                
                for interaction in interactions:
                    severity_color = {
                        "critical": "🔴",
                        "major": "🟡",
                        "moderate": "🟢",
                        "minor": "⚪"
                    }.get(interaction.severity.value, "?")
                    
                    with st.expander(f"{severity_color} {interaction.drug1} + {interaction.drug2}"):
                        st.write(f"**Severity:** {interaction.severity.value.upper()}")
                        st.write(f"**Description:** {interaction.description}")
                        st.write(f"**Recommendation:** {interaction.recommendation}")
    
    # ========== PAGE: REPORTS & EXPORT ==========
    elif page == "Reports & Export":
        st.header("📄 Reports & Data Export")
        
        if not kg.discharge_summary:
            st.warning("⚠️ Please load a patient first")
        else:
            tab1, tab2, tab3 = st.tabs(["Summary Report", "Medication Report", "Export Data"])
            
            with tab1:
                st.subheader("Patient Summary Report")
                summary = kg.get_summary_for_agent()
                st.text(summary)
                
                st.download_button(
                    label="📥 Download Summary",
                    data=summary,
                    file_name=f"summary_{kg.patient_id}.txt",
                    mime="text/plain"
                )
            
            with tab2:
                st.subheader("Medication Summary")
                report = st.session_state.pharmacist_agent.generate_medication_summary_report()
                st.text(report)
                
                st.download_button(
                    label="📥 Download Medication Report",
                    data=report,
                    file_name=f"medications_{kg.patient_id}.txt",
                    mime="text/plain"
                )
            
            with tab3:
                st.subheader("Export Patient Data")
                
                export_format = st.selectbox("Export Format", ["JSON", "CSV", "PDF"])
                
                if export_format == "JSON":
                    json_data = kg.to_json()
                    st.download_button(
                        label="📥 Download as JSON",
                        data=json_data,
                        file_name=f"patient_data_{kg.patient_id}.json",
                        mime="application/json"
                    )
                
                elif export_format == "CSV":
                    # Export medications as CSV
                    meds_df = pd.DataFrame([
                        {
                            "Name": m.name,
                            "Dosage": m.dosage,
                            "Frequency": m.frequency,
                            "Route": m.route,
                            "Indication": m.indication
                        }
                        for m in kg.get_current_medications()
                    ])
                    
                    csv_data = meds_df.to_csv(index=False)
                    st.download_button(
                        label="📥 Download as CSV",
                        data=csv_data,
                        file_name=f"medications_{kg.patient_id}.csv",
                        mime="text/csv"
                    )
                
                elif export_format == "PDF":
                    st.info("PDF export coming soon!")


if __name__ == "__main__":
    main()
