"""
Agent B - The Pharmacist (Logic & Reasoning Agent)
Analyzes medications for dangerous interactions using knowledge base
Provides clinical recommendations based on extracted data

Enhanced with A2A Protocol for agent communication
"""

import json
import time
from datetime import datetime
from typing import Dict, List, Tuple, Optional
from patient_knowledge_graph import (
    PatientKnowledgeGraph,
    DrugInteraction,
    InteractionSeverity,
    AgentAnalysis
)
from a2a_protocol import get_a2a_protocol, MessageType, MessagePriority, Message


class PharmacistAgent:
    """
    Logic-focused agent specialized in medication interaction analysis
    and clinical reasoning based on extracted medical data
    
    Enhanced with A2A Protocol for communication with other agents
    """
    
    def __init__(self, knowledge_graph: PatientKnowledgeGraph):
        self.kg = knowledge_graph
        self.agent_name = "pharmacist"
        
        # A2A Protocol Integration
        self.a2a_protocol = get_a2a_protocol()
        self.a2a_protocol.register_agent(self.agent_name)
        
        # Knowledge base of known drug interactions
        self.interaction_database = self._build_interaction_database()
    
    def _build_interaction_database(self) -> Dict[str, List[Dict]]:
        """
        Build a comprehensive drug interaction knowledge base
        Format: {drug_pair: [interaction_data]}
        """
        return {
            # Anticoagulant interactions (high severity)
            ("warfarin", "aspirin"): {
                "severity": InteractionSeverity.CRITICAL,
                "description": "Significant increased risk of bleeding",
                "recommendation": "Use alternative antiplatelet agent or monitor INR closely. Consider PPI for GI protection.",
                "notes": "Increased risk of GI bleeding especially"
            },
            ("apixaban", "clopidogrel"): {
                "severity": InteractionSeverity.MAJOR,
                "description": "Dual anticoagulation increases bleeding risk",
                "recommendation": "Only use together if clear indication (e.g., post-ACS). Monitor for bleeding signs.",
                "notes": "Most common combination in post-ACS patients"
            },
            
            # Cardiovascular interactions
            ("metoprolol", "verapamil"): {
                "severity": InteractionSeverity.CRITICAL,
                "description": "Risk of severe bradycardia and AV block",
                "recommendation": "Avoid combination or use with extreme caution. Requires ECG monitoring.",
                "notes": "Monitor HR and PR interval"
            },
            ("lisinopril", "potassium"): {
                "severity": InteractionSeverity.MAJOR,
                "description": "Risk of hyperkalemia",
                "recommendation": "Monitor potassium levels regularly. Limit potassium supplementation.",
                "notes": "Check K+ every 3-6 months"
            },
            ("lisinopril", "spironolactone"): {
                "severity": InteractionSeverity.MAJOR,
                "description": "Significant hyperkalemia risk",
                "recommendation": "Use cautiously. Requires regular K+ and renal function monitoring.",
                "notes": "Both drugs increase K+ retention"
            },
            
            # Statin interactions
            ("atorvastatin", "gemfibrozil"): {
                "severity": InteractionSeverity.MAJOR,
                "description": "Increased risk of myopathy and rhabdomyolysis",
                "recommendation": "Consider alternative fibrate (fenofibrate) or reduce statin dose.",
                "notes": "Increased statin levels up to 2x"
            },
            ("atorvastatin", "clarithromycin"): {
                "severity": InteractionSeverity.MODERATE,
                "description": "Increased statin levels - myopathy risk",
                "recommendation": "Use alternative antibiotic if possible. Monitor for muscle symptoms.",
                "notes": "CYP3A4 inhibition"
            },
            
            # Diabetic medication interactions
            ("metformin", "contrast_dye"): {
                "severity": InteractionSeverity.MAJOR,
                "description": "Risk of lactic acidosis with contrast procedures",
                "recommendation": "Hold metformin 48 hours before and after contrast procedures.",
                "notes": "Especially important for renal function < 60 mL/min"
            },
            ("glipizide", "alcohol"): {
                "severity": InteractionSeverity.MODERATE,
                "description": "Increased hypoglycemia risk",
                "recommendation": "Limit alcohol consumption. Educate on hypoglycemia signs.",
                "notes": "Risk of severe hypoglycemia especially with high doses"
            },
            
            # NSAIDs interactions
            ("ibuprofen", "lisinopril"): {
                "severity": InteractionSeverity.MODERATE,
                "description": "Reduced antihypertensive effect and renal risk",
                "recommendation": "Use acetaminophen instead. If NSAID needed, use lowest dose.",
                "notes": "Monitor renal function and BP"
            },
            ("ibuprofen", "warfarin"): {
                "severity": InteractionSeverity.MAJOR,
                "description": "Significantly increased bleeding risk",
                "recommendation": "Avoid NSAIDs. Use acetaminophen for pain relief.",
                "notes": "Both affect coagulation through different mechanisms"
            },
            
            # Respiratory interactions
            ("albuterol", "beta_blocker"): {
                "severity": InteractionSeverity.MODERATE,
                "description": "Beta-blockers can attenuate albuterol bronchodilation",
                "recommendation": "Use cardioselective beta-blockers (metoprolol/atenolol). May need higher albuterol doses.",
                "notes": "Avoid non-selective beta-blockers"
            },
            
            # Psychiatric medication interactions
            ("sertraline", "tramadol"): {
                "severity": InteractionSeverity.MAJOR,
                "description": "Risk of serotonin syndrome",
                "recommendation": "Avoid combination if possible. Monitor for serotonin syndrome symptoms.",
                "notes": "Symptoms: agitation, confusion, rapid HR, high BP"
            },
            
            # Antibiotic interactions
            ("azithromycin", "digoxin"): {
                "severity": InteractionSeverity.MODERATE,
                "description": "Increased digoxin levels - toxicity risk",
                "recommendation": "Monitor digoxin levels. Consider ECG monitoring.",
                "notes": "Azithromycin increases digoxin bioavailability"
            },
            
            # General serious interactions
            ("simvastatin", "amiodarone"): {
                "severity": InteractionSeverity.CRITICAL,
                "description": "Major myopathy risk - simvastatin levels increase significantly",
                "recommendation": "Reduce simvastatin to max 20mg daily or switch to pravastatin.",
                "notes": "CYP3A4 strong inhibition"
            },
        }
    
    def check_medication_interactions(self) -> AgentAnalysis:
        """
        Comprehensive medication interaction analysis
        Compares all medication pairs in patient's regimen
        """
        start_time = time.time()
        analysis = AgentAnalysis(
            agent_name=self.agent_name,
            timestamp=datetime.now().isoformat(),
            status="processing"
        )
        
        try:
            medications = self.kg.get_current_medications()
            interactions_found = []
            
            # Check all medication pairs
            for i, med1 in enumerate(medications):
                for med2 in medications[i+1:]:
                    interaction = self._check_pair(med1.name, med2.name)
                    if interaction:
                        interactions_found.append(interaction)
                        self.kg.add_interaction(interaction)
            
            # Prepare findings
            critical_count = sum(1 for i in interactions_found if i.severity == InteractionSeverity.CRITICAL)
            major_count = sum(1 for i in interactions_found if i.severity == InteractionSeverity.MAJOR)
            moderate_count = sum(1 for i in interactions_found if i.severity == InteractionSeverity.MODERATE)
            
            analysis.findings = {
                "medications_analyzed": len(medications),
                "pairs_checked": len(medications) * (len(medications) - 1) // 2,
                "total_interactions": len(interactions_found),
                "critical_interactions": critical_count,
                "major_interactions": major_count,
                "moderate_interactions": moderate_count,
                "risk_level": self._calculate_overall_risk(interactions_found)
            }
            
            analysis.reasoning = self._generate_clinical_reasoning(
                medications, interactions_found
            )
            
            analysis.recommendations = self._generate_recommendations(interactions_found)
            
            analysis.status = "completed"
            
        except Exception as e:
            analysis.status = "error"
            analysis.error_message = str(e)
            analysis.reasoning = f"Error during interaction analysis: {str(e)}"
        
        analysis.execution_time_seconds = time.time() - start_time
        
        # Store analysis
        self.kg.add_agent_analysis(self.agent_name, analysis)
        
        # A2A Protocol: Send interaction findings to Care Coordinator
        if analysis.status == "completed":
            message_data = {
                "action": "patient_education",
                "total_interactions": analysis.findings.get("total_interactions", 0),
                "critical_interactions": analysis.findings.get("critical_interactions", 0),
                "risk_level": analysis.findings.get("risk_level"),
                "recommendations": analysis.recommendations
            }
            
            self.a2a_protocol.send_request(
                sender=self.agent_name,
                recipient="coordinator",
                action="provide_education",
                data=message_data,
                priority=MessagePriority.HIGH if analysis.findings.get("critical_interactions", 0) > 0 else MessagePriority.NORMAL
            )
        
        return analysis
    
    def _check_pair(self, drug1: str, drug2: str) -> Optional[DrugInteraction]:
        """
        Check if two drugs have a known interaction
        Performs fuzzy matching to handle name variations
        """
        drug_aliases = {
            "lisinopril": ["prinivil", "zestril"],
            "metoprolol": ["lopressor", "toprol"],
            "atorvastatin": ["lipitor"],
            "aspirin": ["asa"],
            "clopidogrel": ["plavix"],
            "apixaban": ["eliquat"],
            "warfarin": ["coumadin"],
        }
        
        # Normalize drug names first
        d1_norm = self._normalize_drug_name(drug1, drug_aliases)
        d2_norm = self._normalize_drug_name(drug2, drug_aliases)
        
        # Direct lookup with normalized names
        for (d1, d2), interaction_data in self.interaction_database.items():
            if (d1_norm == d1 and d2_norm == d2) or \
               (d1_norm == d2 and d2_norm == d1):
                return DrugInteraction(
                    drug1=drug1,
                    drug2=drug2,
                    severity=interaction_data["severity"],
                    description=interaction_data["description"],
                    recommendation=interaction_data["recommendation"]
                )
        
        return None
    
    def _normalize_drug_name(self, drug: str, aliases: Dict) -> str:
        """Normalize drug name to primary generic name"""
        drug_lower = drug.lower().split()[0]
        
        for primary, alt_names in aliases.items():
            if drug_lower == primary or drug_lower in alt_names:
                return primary
        
        return drug.lower()
    
    def _calculate_overall_risk(self, interactions: List[DrugInteraction]) -> str:
        """Calculate overall risk level based on interactions"""
        if not interactions:
            return "LOW"
        
        critical_count = sum(1 for i in interactions if i.severity == InteractionSeverity.CRITICAL)
        major_count = sum(1 for i in interactions if i.severity == InteractionSeverity.MAJOR)
        
        if critical_count > 0:
            return "CRITICAL"
        elif major_count >= 2:
            return "HIGH"
        elif major_count >= 1:
            return "MODERATE"
        else:
            return "LOW"
    
    def _generate_clinical_reasoning(self, medications: List, 
                                   interactions: List[DrugInteraction]) -> str:
        """Generate detailed clinical reasoning"""
        reasoning = f"""
        PHARMACIST ANALYSIS - CLINICAL REASONING:
        
        1. MEDICATION REGIMEN REVIEW:
           - Total medications: {len(medications)}
           - Medication classes: {self._identify_drug_classes(medications)}
        
        2. INTERACTION SCREENING:
           - Pairs checked: {len(medications) * (len(medications) - 1) // 2}
           - Interactions identified: {len(interactions)}
        
        3. RISK STRATIFICATION:
        """
        
        critical = [i for i in interactions if i.severity == InteractionSeverity.CRITICAL]
        major = [i for i in interactions if i.severity == InteractionSeverity.MAJOR]
        moderate = [i for i in interactions if i.severity == InteractionSeverity.MODERATE]
        
        if critical:
            reasoning += f"\n        CRITICAL ({len(critical)}):\n"
            for interaction in critical:
                reasoning += f"        - {interaction.drug1} + {interaction.drug2}: {interaction.description}\n"
        
        if major:
            reasoning += f"\n        MAJOR ({len(major)}):\n"
            for interaction in major:
                reasoning += f"        - {interaction.drug1} + {interaction.drug2}: {interaction.description}\n"
        
        reasoning += f"""
        
        4. CLINICAL CONSIDERATIONS:
           - Patient renal function: [To be reviewed by provider]\n           - Patient hepatic function: [To be reviewed by provider]\n           - Age and comorbidities: [To be reviewed by provider]\n        
        5. RECOMMENDATION PRIORITY:
           - Critical interactions MUST be addressed
           - Major interactions warrant close monitoring
           - Moderate interactions require patient education
        """.strip()
        
        return reasoning
    
    def _identify_drug_classes(self, medications: List) -> str:
        """Identify drug classes in the regimen"""
        drug_classes = set()
        
        class_mapping = {
            "ace_inhibitor": ["lisinopril", "enalapril", "ramipril", "captopril"],
            "beta_blocker": ["metoprolol", "atenolol", "propranolol", "carvedilol"],
            "statin": ["atorvastatin", "simvastatin", "pravastatin", "rosuvastatin"],
            "anticoagulant": ["warfarin", "apixaban", "rivaroxaban", "dabigatran"],
            "antiplatelet": ["aspirin", "clopidogrel", "ticagrelor"],
            "diuretic": ["furosemide", "spironolactone", "hydrochlorothiazide"],
        }
        
        for med in medications:
            med_name = med.name.lower()
            for drug_class, drug_names in class_mapping.items():
                if any(drug in med_name for drug in drug_names):
                    drug_classes.add(drug_class)
        
        return ", ".join(drug_classes) if drug_classes else "Various"
    
    def _generate_recommendations(self, interactions: List[DrugInteraction]) -> List[str]:
        """Generate actionable clinical recommendations"""
        recommendations = []
        
        if not interactions:
            recommendations.append("✅ No known significant drug interactions detected")
            recommendations.append("Continue monitoring for new symptoms or medication changes")
            return recommendations
        
        critical = [i for i in interactions if i.severity == InteractionSeverity.CRITICAL]
        major = [i for i in interactions if i.severity == InteractionSeverity.MAJOR]
        
        if critical:
            recommendations.append(f"🚨 URGENT: {len(critical)} CRITICAL interaction(s) require immediate review by prescribing physician")
            for interaction in critical:
                recommendations.append(f"  • {interaction.recommendation}")
        
        if major:
            recommendations.append(f"⚠️ {len(major)} MAJOR interaction(s) require monitoring:")
            for interaction in major:
                recommendations.append(f"  • {interaction.recommendation}")
        
        recommendations.append("Schedule medication reconciliation appointment with pharmacist")
        recommendations.append("Patient education on medication timing and administration needed")
        recommendations.append("Consider implementing pharmacy-directed therapy protocols")
        
        return recommendations
    
    def generate_medication_summary_report(self) -> str:
        """Generate a comprehensive medication summary report"""
        medications = self.kg.get_current_medications()
        interactions = self.kg.drug_interactions
        
        report = "MEDICATION SUMMARY REPORT\n"
        report += "=" * 50 + "\n\n"
        
        report += f"Total Medications: {len(medications)}\n"
        report += f"Total Interactions: {len(interactions)}\n\n"
        
        report += "CURRENT MEDICATIONS:\n"
        for med in medications:
            report += f"  • {med.name} {med.dosage} {med.frequency}\n"
        
        if interactions:
            report += "\n⚠️ IDENTIFIED INTERACTIONS:\n"
            for interaction in interactions:
                report += f"\n  {interaction.drug1} + {interaction.drug2}\n"
                report += f"  Severity: {interaction.severity.value.upper()}\n"
                report += f"  Details: {interaction.description}\n"
        
        return report
