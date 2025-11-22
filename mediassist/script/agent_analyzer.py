"""
Agent A - The Analyzer (Vision Agent)
Parses medical documents/images into structured JSON data
Simulates vision capabilities with CSV data processing

Enhanced with A2A Protocol for agent communication
"""

import json
import time
from datetime import datetime
from typing import Dict, List, Optional, Any
from patient_knowledge_graph import (
    PatientKnowledgeGraph,
    DischargeSummary,
    MedicationRecord,
    FollowUpTask,
    AgentAnalysis
)
from a2a_protocol import get_a2a_protocol, MessageType, MessagePriority, Message


class AnalyzerAgent:
    """
    Vision-capable agent that extracts and structures medical data
    from discharge summaries and medical documents
    
    Enhanced with A2A Protocol for communication with other agents
    """
    
    def __init__(self, knowledge_graph: PatientKnowledgeGraph):
        self.kg = knowledge_graph
        self.agent_name = "analyzer"
        self.processing_log = []
        
        # A2A Protocol Integration
        self.a2a_protocol = get_a2a_protocol()
        self.a2a_protocol.register_agent(self.agent_name)
    
    def analyze_discharge_summary(self, summary_data: Dict[str, str]) -> AgentAnalysis:
        """
        Parse and structure discharge summary data
        
        Args:
            summary_data: Dictionary with keys like patient_id, name, diagnosis, etc.
        
        Returns:
            AgentAnalysis with structured findings
        """
        start_time = time.time()
        analysis = AgentAnalysis(
            agent_name=self.agent_name,
            timestamp=datetime.now().isoformat(),
            status="processing"
        )
        
        try:
            # Extract discharge summary
            discharge_summary = DischargeSummary(
                patient_id=summary_data.get("patient_id", "UNKNOWN"),
                patient_name=summary_data.get("name", ""),
                admission_date=summary_data.get("admission_date", ""),
                discharge_date=summary_data.get("discharge_date", ""),
                primary_diagnosis=summary_data.get("primary_diagnosis", ""),
                secondary_diagnoses=self._parse_list_field(
                    summary_data.get("secondary_diagnoses", "")
                ),
                hospital_course=summary_data.get("hospital_course", ""),
                discharge_instructions=summary_data.get("discharge_instructions", ""),
                precautions=self._parse_list_field(
                    summary_data.get("precautions", "")
                )
            )
            
            # Store in knowledge graph
            self.kg.set_discharge_summary(discharge_summary)
            
            # Parse medications
            medications = self._extract_medications(
                summary_data.get("medications", "")
            )
            for med in medications:
                self.kg.add_medication(med)
            
            # Extract follow-up information
            follow_ups = self._extract_follow_ups(
                summary_data.get("follow_up", "")
            )
            for task in follow_ups:
                self.kg.add_follow_up(task)
            
            # Extract allergies if provided
            if "allergies" in summary_data:
                allergies = self._parse_list_field(summary_data.get("allergies", ""))
                for allergy in allergies:
                    self.kg.add_allergy(allergy)
            
            # Prepare findings
            analysis.findings = {
                "patient_id": discharge_summary.patient_id,
                "patient_name": discharge_summary.patient_name,
                "diagnosis": discharge_summary.primary_diagnosis,
                "medications_extracted": len(medications),
                "follow_ups_extracted": len(follow_ups),
                "data_quality_score": self._calculate_data_quality(summary_data)
            }
            
            analysis.reasoning = self._generate_reasoning(
                discharge_summary, medications, follow_ups
            )
            
            analysis.recommendations = [
                f"Patient has {len(medications)} medications requiring pharmacist review",
                f"{len(follow_ups)} follow-up appointments scheduled",
                "Monitor for drug-drug interactions",
                "Patient education recommended before care coordinator engagement"
            ]
            
            analysis.status = "completed"
            
        except Exception as e:
            analysis.status = "error"
            analysis.error_message = str(e)
            analysis.reasoning = f"Error during analysis: {str(e)}"
        
        analysis.execution_time_seconds = time.time() - start_time
        
        # Store analysis in knowledge graph
        self.kg.add_agent_analysis(self.agent_name, analysis)
        
        # A2A Protocol: Send analysis to Pharmacist Agent
        if analysis.status == "completed":
            message_data = {
                "action": "analyze_medications",
                "patient_id": analysis.findings.get("patient_id"),
                "medications_count": analysis.findings.get("medications_extracted"),
                "diagnosis": analysis.findings.get("diagnosis"),
                "analysis_results": analysis.findings
            }
            
            self.a2a_protocol.send_request(
                sender=self.agent_name,
                recipient="pharmacist",
                action="analyze_medications",
                data=message_data,
                priority=MessagePriority.HIGH
            )
        
        return analysis
    
    def _parse_list_field(self, field_value: str) -> List[str]:
        """
        Parse comma-separated string into list
        Handles various formats and cleans whitespace
        """
        if not field_value or not isinstance(field_value, str):
            return []
        
        items = [item.strip() for item in field_value.split(",") if item.strip()]
        return items
    
    def _extract_medications(self, med_text: str) -> List[MedicationRecord]:
        """
        Extract medications from text
        Supports various formats: "Name Dosage Frequency" or "Name, Dosage, Frequency"
        """
        medications = []
        
        if not med_text:
            return medications
        
        # Split by comma or newline
        med_entries = [m.strip() for m in med_text.replace(";", ",").split(",") if m.strip()]
        
        for entry in med_entries:
            parts = entry.split()
            if len(parts) >= 1:
                med = MedicationRecord(
                    name=parts[0],
                    dosage=parts[1] if len(parts) > 1 else "as prescribed",
                    frequency=parts[2] if len(parts) > 2 else "per label",
                    route="oral",
                    start_date=datetime.now().isoformat(),
                    indication="Post-discharge management"
                )
                medications.append(med)
        
        return medications
    
    def _extract_follow_ups(self, follow_up_text: str) -> List[FollowUpTask]:
        """
        Extract follow-up appointments from text
        Format: "Specialty in N days/weeks" or "Appointment on YYYY-MM-DD"
        """
        follow_ups = []
        
        if not follow_up_text:
            return follow_ups
        
        # Common follow-up patterns
        specialties = ["Cardiology", "Neurology", "Orthopedics", "Pulmonology", 
                       "Endocrinology", "Gastroenterology", "Psychiatry", "PCP"]
        
        for specialty in specialties:
            if specialty.lower() in follow_up_text.lower():
                # Extract timing information
                timing = "1 week"
                if "week" in follow_up_text.lower():
                    for word in follow_up_text.split():
                        if word.isdigit():
                            timing = f"{word} week(s)"
                            break
                
                task = FollowUpTask(
                    task_type="appointment",
                    description=f"{specialty} follow-up appointment",
                    scheduled_date="",
                    specialty=specialty,
                    priority="high"
                )
                follow_ups.append(task)
        
        return follow_ups
    
    def _calculate_data_quality(self, data: Dict[str, str]) -> float:
        """
        Calculate a quality score for the extracted data (0-100)
        Based on completeness and consistency
        """
        required_fields = ["patient_id", "name", "primary_diagnosis", "medications"]
        present_fields = sum(1 for field in required_fields if field in data and data[field])
        
        score = (present_fields / len(required_fields)) * 100
        return round(score, 1)
    
    def _generate_reasoning(self, discharge: DischargeSummary, 
                          medications: List[MedicationRecord],
                          follow_ups: List[FollowUpTask]) -> str:
        """
        Generate human-readable reasoning for the analysis
        """
        reasoning = f"""
        ANALYSIS REASONING:
        
        1. PATIENT IDENTIFICATION:
           - Successfully identified patient: {discharge.patient_name} (ID: {discharge.patient_id})
           - Discharge date: {discharge.discharge_date}
        
        2. DIAGNOSIS EXTRACTION:
           - Primary: {discharge.primary_diagnosis}
           - Secondary: {', '.join(discharge.secondary_diagnoses) if discharge.secondary_diagnoses else 'None'}
        
        3. MEDICATION PARSING:
           - {len(medications)} medications extracted and normalized
           - All medications stored for interaction checking
        
        4. FOLLOW-UP PLANNING:
           - {len(follow_ups)} follow-up appointments identified
           - Specialties involved: {', '.join(set(f.specialty for f in follow_ups))}
        
        5. DATA QUALITY:
           - Completeness score: {self._calculate_data_quality({
               'patient_id': discharge.patient_id,
               'name': discharge.patient_name,
               'primary_diagnosis': discharge.primary_diagnosis,
               'medications': str(medications)
           })}%
           - All critical fields present and properly formatted
        
        NEXT STEPS:
        - Pass to Pharmacist Agent for medication interaction analysis
        - Prepare for Care Coordinator engagement
        """.strip()
        
        return reasoning
    
    def process_csv_row(self, row_data: Dict[str, str]) -> AgentAnalysis:
        """
        Process a single row from discharge summaries CSV
        Wrapper for analyze_discharge_summary
        """
        return self.analyze_discharge_summary(row_data)
    
    def batch_process(self, data_list: List[Dict[str, str]]) -> List[AgentAnalysis]:
        """
        Process multiple discharge summaries
        Returns list of analyses for each record
        """
        analyses = []
        for data in data_list:
            analysis = self.analyze_discharge_summary(data)
            analyses.append(analysis)
            time.sleep(0.1)  # Simulate processing delay
        
        return analyses


def create_mock_discharge_data() -> Dict[str, str]:
    """
    Create mock discharge data for testing
    Simulates real discharge summary
    """
    return {
        "patient_id": "P001",
        "name": "John Smith",
        "age": "45",
        "admission_date": "2025-02-01",
        "discharge_date": "2025-02-07",
        "primary_diagnosis": "Acute Myocardial Infarction (AMI) - STEMI",
        "secondary_diagnoses": "Hypertension, Hyperlipidemia, Type 2 Diabetes",
        "hospital_course": "Patient presented with chest pain and was diagnosed with STEMI. Underwent emergent cardiac catheterization with stent placement. Course complicated by transient heart failure. Treated with dual antiplatelet therapy and aggressive lipid management. Discharged in stable condition.",
        "medications": "Aspirin 325mg daily, Clopidogrel 75mg daily, Metoprolol 50mg twice daily, Lisinopril 10mg daily, Atorvastatin 80mg daily, Sublingual nitroglycerin as needed",
        "follow_up": "Cardiology in 1 week, Primary Care in 3 days",
        "allergies": "NKDA",
        "precautions": "No smoking, Low sodium diet, Monitor for chest pain, Avoid strenuous activity for 4 weeks",
        "discharge_instructions": "Take all medications as prescribed. Avoid heavy lifting. Contact doctor if experiencing chest pain, shortness of breath, or excessive sweating."
    }
