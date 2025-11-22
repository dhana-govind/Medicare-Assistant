"""
Patient Knowledge Graph Module - State Management for MediSync
Manages shared data structure between all three agents
"""

from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum
import json


class InteractionSeverity(Enum):
    """Severity levels for drug interactions"""
    CRITICAL = "critical"
    MAJOR = "major"
    MODERATE = "moderate"
    MINOR = "minor"
    NONE = "none"


@dataclass
class MedicationRecord:
    """Represents a single medication"""
    name: str
    dosage: str
    frequency: str
    route: str = "oral"
    start_date: str = ""
    indication: str = ""
    notes: str = ""
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class DrugInteraction:
    """Represents a drug-drug interaction"""
    drug1: str
    drug2: str
    severity: InteractionSeverity
    description: str
    recommendation: str
    source: str = "interaction_database"
    
    def to_dict(self) -> Dict:
        return {
            **asdict(self),
            "severity": self.severity.value
        }


@dataclass
class FollowUpTask:
    """Represents a follow-up appointment or task"""
    task_type: str  # "appointment", "lab_test", "medication_refill", "assessment"
    description: str
    scheduled_date: str
    specialty: str = ""
    priority: str = "normal"
    completed: bool = False
    notes: str = ""
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class DischargeSummary:
    """Represents extracted discharge summary data"""
    patient_id: str
    patient_name: str
    admission_date: str
    discharge_date: str
    primary_diagnosis: str
    secondary_diagnoses: List[str] = field(default_factory=list)
    hospital_course: str = ""
    discharge_instructions: str = ""
    precautions: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class AgentAnalysis:
    """Represents analysis from an agent"""
    agent_name: str
    timestamp: str
    status: str  # "pending", "processing", "completed", "error"
    findings: Dict[str, Any] = field(default_factory=dict)
    reasoning: str = ""
    recommendations: List[str] = field(default_factory=list)
    error_message: str = ""
    execution_time_seconds: float = 0.0
    
    def to_dict(self) -> Dict:
        return asdict(self)


class PatientKnowledgeGraph:
    """
    Central data structure managing all patient information and agent analyses
    Implements state management for multi-agent orchestration
    """
    
    def __init__(self, patient_id: str = ""):
        self.patient_id = patient_id
        self.created_at = datetime.now().isoformat()
        self.last_updated = datetime.now().isoformat()
        
        # Core patient data
        self.discharge_summary: Optional[DischargeSummary] = None
        
        # Medications
        self.current_medications: List[MedicationRecord] = []
        self.previous_medications: List[MedicationRecord] = []
        
        # Interactions
        self.drug_interactions: List[DrugInteraction] = []
        self.allergy_list: List[str] = []
        
        # Follow-ups
        self.follow_up_tasks: List[FollowUpTask] = []
        
        # Agent analyses (persistent tracking)
        self.agent_analyses: Dict[str, List[AgentAnalysis]] = {
            "analyzer": [],
            "pharmacist": [],
            "care_coordinator": []
        }
        
        # Activity log for UI visualization
        self.activity_log: List[Dict[str, Any]] = []
        
        # Conversation history
        self.conversation_history: List[Dict[str, str]] = []
    
    # ========== Discharge Summary Methods ==========
    
    def set_discharge_summary(self, summary: DischargeSummary) -> None:
        """Store parsed discharge summary"""
        self.discharge_summary = summary
        self.patient_id = summary.patient_id
        self._log_activity("Discharge summary loaded", "analyzer", "success")
        self.last_updated = datetime.now().isoformat()
    
    def get_discharge_summary(self) -> Optional[DischargeSummary]:
        """Retrieve discharge summary"""
        return self.discharge_summary
    
    # ========== Medication Management ==========
    
    def add_medication(self, medication: MedicationRecord) -> None:
        """Add a new medication"""
        self.current_medications.append(medication)
        self._log_activity(f"Medication added: {medication.name}", "system", "info")
        self.last_updated = datetime.now().isoformat()
    
    def get_current_medications(self) -> List[MedicationRecord]:
        """Get all current medications"""
        return self.current_medications
    
    def remove_medication(self, med_name: str) -> bool:
        """Remove a medication by name"""
        original_count = len(self.current_medications)
        self.current_medications = [m for m in self.current_medications if m.name.lower() != med_name.lower()]
        if len(self.current_medications) < original_count:
            self._log_activity(f"Medication removed: {med_name}", "system", "info")
            self.last_updated = datetime.now().isoformat()
            return True
        return False
    
    def get_medication_by_name(self, name: str) -> Optional[MedicationRecord]:
        """Find medication by name"""
        for med in self.current_medications:
            if med.name.lower() == name.lower():
                return med
        return None
    
    # ========== Drug Interaction Management ==========
    
    def add_interaction(self, interaction: DrugInteraction) -> None:
        """Add a detected drug interaction"""
        self.drug_interactions.append(interaction)
        self._log_activity(
            f"Interaction detected: {interaction.drug1} + {interaction.drug2} ({interaction.severity.value})",
            "pharmacist",
            "warning" if interaction.severity.value in ["critical", "major"] else "info"
        )
        self.last_updated = datetime.now().isoformat()
    
    def get_interactions_by_severity(self, severity: InteractionSeverity) -> List[DrugInteraction]:
        """Get interactions filtered by severity"""
        return [i for i in self.drug_interactions if i.severity == severity]
    
    def get_critical_interactions(self) -> List[DrugInteraction]:
        """Get all critical interactions"""
        return self.get_interactions_by_severity(InteractionSeverity.CRITICAL)
    
    def clear_interactions(self) -> None:
        """Clear all detected interactions"""
        self.drug_interactions = []
    
    # ========== Allergy Management ==========
    
    def add_allergy(self, allergy: str) -> None:
        """Add allergy information"""
        if allergy.lower() not in [a.lower() for a in self.allergy_list]:
            self.allergy_list.append(allergy)
            self._log_activity(f"Allergy recorded: {allergy}", "system", "warning")
            self.last_updated = datetime.now().isoformat()
    
    def get_allergies(self) -> List[str]:
        """Get all recorded allergies"""
        return self.allergy_list
    
    # ========== Follow-up Management ==========
    
    def add_follow_up(self, task: FollowUpTask) -> None:
        """Add a follow-up task"""
        self.follow_up_tasks.append(task)
        self._log_activity(f"Follow-up scheduled: {task.description}", "care_coordinator", "info")
        self.last_updated = datetime.now().isoformat()
    
    def get_pending_follow_ups(self) -> List[FollowUpTask]:
        """Get all pending follow-up tasks"""
        return [t for t in self.follow_up_tasks if not t.completed]
    
    def complete_follow_up(self, index: int) -> bool:
        """Mark a follow-up as completed"""
        if 0 <= index < len(self.follow_up_tasks):
            self.follow_up_tasks[index].completed = True
            self._log_activity("Follow-up marked as completed", "system", "success")
            self.last_updated = datetime.now().isoformat()
            return True
        return False
    
    # ========== Agent Analysis Tracking ==========
    
    def add_agent_analysis(self, agent_name: str, analysis: AgentAnalysis) -> None:
        """Store analysis from an agent"""
        if agent_name in self.agent_analyses:
            self.agent_analyses[agent_name].append(analysis)
            self._log_activity(f"Analysis from {agent_name}: {analysis.status}", agent_name, "info")
            self.last_updated = datetime.now().isoformat()
    
    def get_agent_analyses(self, agent_name: str) -> List[AgentAnalysis]:
        """Retrieve all analyses from a specific agent"""
        return self.agent_analyses.get(agent_name, [])
    
    def get_latest_agent_analysis(self, agent_name: str) -> Optional[AgentAnalysis]:
        """Get the most recent analysis from an agent"""
        analyses = self.get_agent_analyses(agent_name)
        return analyses[-1] if analyses else None
    
    # ========== Activity Log (for UI visualization) ==========
    
    def _log_activity(self, message: str, source: str, level: str) -> None:
        """Log an activity for real-time visualization"""
        self.activity_log.append({
            "timestamp": datetime.now().isoformat(),
            "message": message,
            "source": source,
            "level": level  # "info", "warning", "success", "error"
        })
        # Keep only last 100 activities
        self.activity_log = self.activity_log[-100:]
    
    def get_activity_log(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Retrieve recent activities"""
        return self.activity_log[-limit:]
    
    # ========== Conversation History ==========
    
    def add_conversation(self, user_message: str, assistant_message: str, agent_name: str = "care_coordinator") -> None:
        """Add to conversation history"""
        self.conversation_history.append({
            "timestamp": datetime.now().isoformat(),
            "user": user_message,
            "assistant": assistant_message,
            "agent": agent_name
        })
        self.last_updated = datetime.now().isoformat()
    
    def get_conversation_history(self, limit: int = 20) -> List[Dict[str, str]]:
        """Get recent conversation history"""
        return self.conversation_history[-limit:]
    
    # ========== Export/Import Methods ==========
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert entire knowledge graph to dictionary"""
        return {
            "patient_id": self.patient_id,
            "created_at": self.created_at,
            "last_updated": self.last_updated,
            "discharge_summary": self.discharge_summary.to_dict() if self.discharge_summary else None,
            "current_medications": [m.to_dict() for m in self.current_medications],
            "previous_medications": [m.to_dict() for m in self.previous_medications],
            "drug_interactions": [i.to_dict() for i in self.drug_interactions],
            "allergies": self.allergy_list,
            "follow_up_tasks": [t.to_dict() for t in self.follow_up_tasks],
            "activity_log": self.get_activity_log(),
            "conversation_history": self.get_conversation_history()
        }
    
    def to_json(self) -> str:
        """Export as JSON string"""
        return json.dumps(self.to_dict(), indent=2, default=str)
    
    def get_summary_for_agent(self) -> str:
        """Generate a formatted summary for agent consumption"""
        summary_parts = []
        
        if self.discharge_summary:
            summary_parts.append(f"PATIENT: {self.discharge_summary.patient_name}")
            summary_parts.append(f"DIAGNOSIS: {self.discharge_summary.primary_diagnosis}")
            if self.discharge_summary.secondary_diagnoses:
                summary_parts.append(f"COMORBIDITIES: {', '.join(self.discharge_summary.secondary_diagnoses)}")
        
        if self.current_medications:
            summary_parts.append("\nCURRENT MEDICATIONS:")
            for med in self.current_medications:
                summary_parts.append(f"  - {med.name} {med.dosage} {med.frequency}")
        
        if self.allergy_list:
            summary_parts.append(f"\nALLERGIES: {', '.join(self.allergy_list)}")
        
        if self.drug_interactions:
            critical = self.get_critical_interactions()
            if critical:
                summary_parts.append(f"\n⚠️ CRITICAL INTERACTIONS: {len(critical)} detected")
        
        if self.follow_up_tasks:
            pending = self.get_pending_follow_ups()
            if pending:
                summary_parts.append(f"\nPENDING FOLLOW-UPS: {len(pending)}")
        
        return "\n".join(summary_parts)
