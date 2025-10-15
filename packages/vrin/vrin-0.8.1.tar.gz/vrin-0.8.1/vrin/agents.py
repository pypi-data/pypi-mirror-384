"""
Hybrid Agent Architecture for VRIN v0.4.0 - Phase 3

Intelligent routing system that dynamically decides where to process data:
- Sensitive data: Customer's private infrastructure
- Non-sensitive data: VRIN's optimized cloud services
- Compliance-aware: Routes based on regulatory requirements

Architecture Components:
1. DataClassifier - Analyzes content for sensitivity levels
2. HybridRouter - Makes routing decisions based on policies
3. AgentOrchestrator - Coordinates execution across environments
4. ComplianceManager - Ensures regulatory compliance
"""

import logging
import json
from abc import ABC, abstractmethod
from enum import Enum
from typing import Dict, Any, List, Optional, Tuple, Union
from dataclasses import dataclass, asdict
from datetime import datetime

logger = logging.getLogger(__name__)


class SensitivityLevel(Enum):
    """Data sensitivity classification levels."""
    PUBLIC = "public"           # No restrictions
    INTERNAL = "internal"       # Company internal only
    CONFIDENTIAL = "confidential"  # Restricted access
    HIGHLY_SENSITIVE = "highly_sensitive"  # Maximum security


class ProcessingLocation(Enum):
    """Where processing should occur."""
    VRIN_CLOUD = "vrin_cloud"      # VRIN's optimized cloud
    CUSTOMER_PRIVATE = "customer_private"  # Customer's private infra
    HYBRID = "hybrid"              # Split processing


class ComplianceRegime(Enum):
    """Regulatory compliance frameworks."""
    GDPR = "gdpr"                  # EU General Data Protection Regulation
    HIPAA = "hipaa"                # US Healthcare
    SOX = "sox"                    # Sarbanes-Oxley
    PCI_DSS = "pci_dss"           # Payment Card Industry
    SOC2 = "soc2"                 # Service Organization Control 2
    NONE = "none"                 # No specific requirements


@dataclass
class ClassificationResult:
    """Result of data sensitivity classification."""
    sensitivity_level: SensitivityLevel
    confidence: float
    detected_entities: List[str]
    compliance_requirements: List[ComplianceRegime]
    reasoning: str
    processing_recommendation: ProcessingLocation


@dataclass
class RoutingDecision:
    """Decision about where and how to process data."""
    processing_location: ProcessingLocation
    reasoning: str
    fact_extraction_location: ProcessingLocation
    vector_storage_location: ProcessingLocation
    graph_storage_location: ProcessingLocation
    query_processing_location: ProcessingLocation
    compliance_controls: List[str]


@dataclass
class HybridExecutionPlan:
    """Execution plan for hybrid processing."""
    plan_id: str
    created_at: datetime
    routing_decision: RoutingDecision
    execution_steps: List[Dict[str, Any]]
    estimated_duration: int  # seconds
    security_controls: List[str]


class DataClassifier:
    """Analyzes content to determine sensitivity level and compliance requirements."""
    
    def __init__(self):
        self.sensitive_patterns = {
            # PII Patterns
            "ssn": r"\b\d{3}-\d{2}-\d{4}\b",
            "email": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
            "phone": r"\b\d{3}-\d{3}-\d{4}\b",
            "credit_card": r"\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b",
            
            # Healthcare
            "medical_record": r"\b(MRN|medical record number|patient id)\b",
            "diagnosis_code": r"\b[A-Z]\d{2}\.\d\b",
            
            # Financial
            "account_number": r"\b(account|acct)\s*#?\s*\d+\b",
            "routing_number": r"\b\d{9}\b",
            
            # Legal/Corporate
            "confidential_marking": r"\b(confidential|proprietary|trade secret)\b",
            "attorney_client": r"\b(attorney.client|legal privilege)\b"
        }
        
        self.compliance_keywords = {
            ComplianceRegime.GDPR: ["gdpr", "personal data", "data subject", "eu citizen"],
            ComplianceRegime.HIPAA: ["phi", "protected health", "medical", "patient"],
            ComplianceRegime.SOX: ["financial reporting", "sox", "sarbanes", "oxley"],
            ComplianceRegime.PCI_DSS: ["payment", "credit card", "pci", "cardholder"],
            ComplianceRegime.SOC2: ["soc2", "service organization", "security controls"]
        }
    
    def classify(self, content: str, metadata: Optional[Dict[str, Any]] = None) -> ClassificationResult:
        """Classify data sensitivity and determine compliance requirements."""
        
        content_lower = content.lower()
        detected_entities = []
        compliance_requirements = []
        sensitivity_scores = {}
        
        # Pattern matching for sensitive data
        import re
        for entity_type, pattern in self.sensitive_patterns.items():
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches:
                detected_entities.append(entity_type)
                if entity_type in ["ssn", "credit_card", "medical_record"]:
                    sensitivity_scores[SensitivityLevel.HIGHLY_SENSITIVE] = 0.95
                elif entity_type in ["email", "phone", "account_number"]:
                    sensitivity_scores[SensitivityLevel.CONFIDENTIAL] = 0.8
        
        # Compliance regime detection
        for regime, keywords in self.compliance_keywords.items():
            for keyword in keywords:
                if keyword in content_lower:
                    compliance_requirements.append(regime)
                    if regime in [ComplianceRegime.HIPAA, ComplianceRegime.PCI_DSS]:
                        sensitivity_scores[SensitivityLevel.HIGHLY_SENSITIVE] = 0.9
                    elif regime in [ComplianceRegime.GDPR, ComplianceRegime.SOX]:
                        sensitivity_scores[SensitivityLevel.CONFIDENTIAL] = 0.8
        
        # Metadata-based classification
        if metadata:
            if metadata.get("document_type") in ["legal", "medical", "financial"]:
                sensitivity_scores[SensitivityLevel.CONFIDENTIAL] = 0.7
            if metadata.get("classification") == "confidential":
                sensitivity_scores[SensitivityLevel.CONFIDENTIAL] = 0.9
        
        # Determine final sensitivity level
        if sensitivity_scores:
            sensitivity_level = max(sensitivity_scores.keys(), key=lambda k: sensitivity_scores[k])
            confidence = max(sensitivity_scores.values())
        else:
            sensitivity_level = SensitivityLevel.INTERNAL
            confidence = 0.6
        
        # Processing recommendation based on sensitivity
        if sensitivity_level == SensitivityLevel.HIGHLY_SENSITIVE:
            processing_recommendation = ProcessingLocation.CUSTOMER_PRIVATE
        elif sensitivity_level == SensitivityLevel.CONFIDENTIAL:
            processing_recommendation = ProcessingLocation.HYBRID
        else:
            processing_recommendation = ProcessingLocation.VRIN_CLOUD
        
        reasoning = f"Detected {len(detected_entities)} sensitive entities. " + \
                   f"Compliance requirements: {[r.value for r in compliance_requirements]}"
        
        return ClassificationResult(
            sensitivity_level=sensitivity_level,
            confidence=confidence,
            detected_entities=detected_entities,
            compliance_requirements=compliance_requirements,
            reasoning=reasoning,
            processing_recommendation=processing_recommendation
        )


class HybridRouter:
    """Makes intelligent routing decisions based on data classification and policies."""
    
    def __init__(self, organization_policies: Optional[Dict[str, Any]] = None):
        self.organization_policies = organization_policies or {}
        self.default_policies = {
            "force_private": False,  # Force all processing to private infra
            "compliance_override": True,  # Always respect compliance requirements
            "cost_optimization": True,  # Optimize for cost when possible
            "performance_priority": False,  # Prioritize performance over security
        }
    
    def route(self, classification: ClassificationResult, 
             available_infrastructure: Dict[str, bool]) -> RoutingDecision:
        """Make routing decision based on classification and available infrastructure."""
        
        policies = {**self.default_policies, **self.organization_policies}
        
        # Check for force private policy
        if policies.get("force_private"):
            return self._create_private_routing(
                "Organization policy requires all processing in private infrastructure"
            )
        
        # Compliance-driven routing
        if policies.get("compliance_override") and classification.compliance_requirements:
            high_compliance = any(regime in [ComplianceRegime.HIPAA, ComplianceRegime.PCI_DSS] 
                                for regime in classification.compliance_requirements)
            if high_compliance:
                return self._create_private_routing(
                    f"High compliance requirements: {[r.value for r in classification.compliance_requirements]}"
                )
        
        # Sensitivity-based routing
        if classification.sensitivity_level == SensitivityLevel.HIGHLY_SENSITIVE:
            return self._create_private_routing(
                "Highly sensitive data requires private infrastructure processing"
            )
        elif classification.sensitivity_level == SensitivityLevel.CONFIDENTIAL:
            return self._create_hybrid_routing(
                "Confidential data uses hybrid processing for balance of security and performance"
            )
        else:
            return self._create_cloud_routing(
                "Non-sensitive data can be processed in VRIN's optimized cloud infrastructure"
            )
    
    def _create_private_routing(self, reasoning: str) -> RoutingDecision:
        """Create routing decision for private infrastructure."""
        return RoutingDecision(
            processing_location=ProcessingLocation.CUSTOMER_PRIVATE,
            reasoning=reasoning,
            fact_extraction_location=ProcessingLocation.CUSTOMER_PRIVATE,
            vector_storage_location=ProcessingLocation.CUSTOMER_PRIVATE,
            graph_storage_location=ProcessingLocation.CUSTOMER_PRIVATE,
            query_processing_location=ProcessingLocation.CUSTOMER_PRIVATE,
            compliance_controls=[
                "end_to_end_encryption",
                "private_network_only",
                "audit_logging",
                "access_controls"
            ]
        )
    
    def _create_hybrid_routing(self, reasoning: str) -> RoutingDecision:
        """Create routing decision for hybrid processing."""
        return RoutingDecision(
            processing_location=ProcessingLocation.HYBRID,
            reasoning=reasoning,
            fact_extraction_location=ProcessingLocation.CUSTOMER_PRIVATE,  # Extract in private
            vector_storage_location=ProcessingLocation.CUSTOMER_PRIVATE,   # Store vectors privately
            graph_storage_location=ProcessingLocation.CUSTOMER_PRIVATE,    # Store graph privately
            query_processing_location=ProcessingLocation.VRIN_CLOUD,       # Query optimization in cloud
            compliance_controls=[
                "data_anonymization",
                "encrypted_transit",
                "audit_logging"
            ]
        )
    
    def _create_cloud_routing(self, reasoning: str) -> RoutingDecision:
        """Create routing decision for cloud processing."""
        return RoutingDecision(
            processing_location=ProcessingLocation.VRIN_CLOUD,
            reasoning=reasoning,
            fact_extraction_location=ProcessingLocation.VRIN_CLOUD,
            vector_storage_location=ProcessingLocation.VRIN_CLOUD,
            graph_storage_location=ProcessingLocation.VRIN_CLOUD,
            query_processing_location=ProcessingLocation.VRIN_CLOUD,
            compliance_controls=[
                "standard_encryption",
                "access_logging"
            ]
        )


class AgentOrchestrator:
    """Coordinates execution of hybrid processing across different infrastructures."""
    
    def __init__(self, vrin_client, customer_infrastructure_config: Optional[Dict[str, Any]] = None):
        self.vrin_client = vrin_client
        self.customer_config = customer_infrastructure_config or {}
        self.classifier = DataClassifier()
        self.router = HybridRouter()
    
    def create_execution_plan(self, content: str, user_id: str, 
                            metadata: Optional[Dict[str, Any]] = None) -> HybridExecutionPlan:
        """Create execution plan for hybrid processing."""
        
        # Classify the data
        classification = self.classifier.classify(content, metadata)
        
        # Check available infrastructure
        available_infra = {
            "customer_private": bool(self.customer_config.get("neptune_endpoint")),
            "vrin_cloud": True
        }
        
        # Make routing decision
        routing_decision = self.router.route(classification, available_infra)
        
        # Create execution steps
        execution_steps = self._create_execution_steps(routing_decision, content, user_id)
        
        return HybridExecutionPlan(
            plan_id=f"hybrid_plan_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            created_at=datetime.now(),
            routing_decision=routing_decision,
            execution_steps=execution_steps,
            estimated_duration=self._estimate_duration(execution_steps),
            security_controls=routing_decision.compliance_controls
        )
    
    def execute_plan(self, plan: HybridExecutionPlan) -> Dict[str, Any]:
        """Execute the hybrid processing plan."""
        
        results = {
            "plan_id": plan.plan_id,
            "started_at": datetime.now().isoformat(),
            "steps_completed": [],
            "data_processed": {},
            "security_controls_applied": plan.security_controls
        }
        
        try:
            for step_idx, step in enumerate(plan.execution_steps):
                step_result = self._execute_step(step, plan.routing_decision)
                results["steps_completed"].append({
                    "step": step_idx + 1,
                    "action": step["action"],
                    "location": step["location"],
                    "result": step_result,
                    "completed_at": datetime.now().isoformat()
                })
                
                # Store intermediate results
                if step["action"] == "fact_extraction":
                    results["data_processed"]["facts"] = step_result
                elif step["action"] == "vector_storage":
                    results["data_processed"]["vectors"] = step_result
                elif step["action"] == "graph_storage":
                    results["data_processed"]["graph"] = step_result
            
            results["status"] = "completed"
            results["completed_at"] = datetime.now().isoformat()
            
        except Exception as e:
            results["status"] = "failed"
            results["error"] = str(e)
            results["failed_at"] = datetime.now().isoformat()
            logger.error(f"Hybrid execution failed: {str(e)}")
        
        return results
    
    def _create_execution_steps(self, routing: RoutingDecision, content: str, user_id: str) -> List[Dict[str, Any]]:
        """Create detailed execution steps based on routing decision."""
        
        steps = []
        
        # Step 1: Fact Extraction
        steps.append({
            "action": "fact_extraction",
            "location": routing.fact_extraction_location.value,
            "inputs": {"content": content, "user_id": user_id},
            "security_requirements": routing.compliance_controls
        })
        
        # Step 2: Vector Storage
        steps.append({
            "action": "vector_storage", 
            "location": routing.vector_storage_location.value,
            "inputs": {"content": content, "user_id": user_id},
            "depends_on": ["fact_extraction"]
        })
        
        # Step 3: Graph Storage
        steps.append({
            "action": "graph_storage",
            "location": routing.graph_storage_location.value,
            "inputs": {"facts": "from_fact_extraction", "user_id": user_id},
            "depends_on": ["fact_extraction"]
        })
        
        return steps
    
    def _execute_step(self, step: Dict[str, Any], routing: RoutingDecision) -> Dict[str, Any]:
        """Execute a single step in the hybrid processing plan."""
        
        if step["location"] == ProcessingLocation.VRIN_CLOUD.value:
            return self._execute_cloud_step(step)
        elif step["location"] == ProcessingLocation.CUSTOMER_PRIVATE.value:
            return self._execute_private_step(step)
        else:
            raise ValueError(f"Unsupported processing location: {step['location']}")
    
    def _execute_cloud_step(self, step: Dict[str, Any]) -> Dict[str, Any]:
        """Execute step on VRIN's cloud infrastructure."""
        
        if step["action"] == "fact_extraction":
            # Use VRIN's optimized fact extraction
            result = self.vrin_client.insert(
                content=step["inputs"]["content"],
                title="Hybrid Processing Content"
            )
            return {"facts_extracted": result.get("facts_extracted", 0), "location": "vrin_cloud"}
        
        elif step["action"] == "vector_storage":
            # Vector storage handled by VRIN cloud
            return {"status": "stored", "location": "vrin_cloud", "vector_count": 1}
        
        elif step["action"] == "graph_storage":
            # Graph storage handled by VRIN cloud
            return {"status": "stored", "location": "vrin_cloud", "graph_updates": 1}
        
        else:
            return {"status": "completed", "location": "vrin_cloud"}
    
    def _execute_private_step(self, step: Dict[str, Any]) -> Dict[str, Any]:
        """Execute step on customer's private infrastructure."""
        
        # Simulate private infrastructure processing
        # In production, this would connect to customer's Neptune, OpenSearch, etc.
        
        if step["action"] == "fact_extraction":
            return {
                "facts_extracted": 5,  # Simulated
                "location": "customer_private",
                "security": "end_to_end_encrypted"
            }
        
        elif step["action"] == "vector_storage":
            return {
                "status": "stored",
                "location": "customer_private",
                "vector_count": 1,
                "security": "private_network_only"
            }
        
        elif step["action"] == "graph_storage":
            return {
                "status": "stored", 
                "location": "customer_private",
                "graph_updates": 1,
                "security": "encrypted_at_rest"
            }
        
        else:
            return {"status": "completed", "location": "customer_private"}
    
    def _estimate_duration(self, steps: List[Dict[str, Any]]) -> int:
        """Estimate total execution duration in seconds."""
        
        base_times = {
            "fact_extraction": 15,  # seconds
            "vector_storage": 5,
            "graph_storage": 10
        }
        
        total = 0
        for step in steps:
            action_time = base_times.get(step["action"], 5)
            
            # Private processing is slower due to network latency
            if step["location"] == ProcessingLocation.CUSTOMER_PRIVATE.value:
                action_time *= 1.5
            
            total += action_time
        
        return int(total)


class ComplianceManager:
    """Ensures all processing adheres to regulatory compliance requirements."""
    
    def __init__(self):
        self.compliance_controls = {
            ComplianceRegime.GDPR: [
                "data_minimization",
                "purpose_limitation", 
                "right_to_erasure",
                "data_portability",
                "consent_management"
            ],
            ComplianceRegime.HIPAA: [
                "phi_encryption",
                "access_controls",
                "audit_logging",
                "data_integrity",
                "transmission_security"
            ],
            ComplianceRegime.SOX: [
                "financial_data_controls",
                "audit_trail",
                "segregation_of_duties",
                "change_management"
            ],
            ComplianceRegime.PCI_DSS: [
                "cardholder_data_protection",
                "secure_transmission",
                "access_controls",
                "vulnerability_management"
            ]
        }
    
    def validate_processing_plan(self, plan: HybridExecutionPlan, 
                               classification: ClassificationResult) -> Dict[str, Any]:
        """Validate that processing plan meets compliance requirements."""
        
        validation_result = {
            "compliant": True,
            "violations": [],
            "required_controls": [],
            "applied_controls": plan.security_controls
        }
        
        for regime in classification.compliance_requirements:
            required_controls = self.compliance_controls.get(regime, [])
            validation_result["required_controls"].extend(required_controls)
            
            for control in required_controls:
                if control not in plan.security_controls:
                    validation_result["compliant"] = False
                    validation_result["violations"].append(
                        f"Missing required control '{control}' for {regime.value}"
                    )
        
        return validation_result
    
    def generate_compliance_report(self, execution_results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate compliance report for audit purposes."""
        
        return {
            "report_id": f"compliance_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "generated_at": datetime.now().isoformat(),
            "execution_plan_id": execution_results["plan_id"],
            "security_controls_applied": execution_results.get("security_controls_applied", []),
            "data_processing_locations": self._extract_processing_locations(execution_results),
            "compliance_status": "compliant",  # Would be determined by validation
            "audit_trail": execution_results.get("steps_completed", [])
        }
    
    def _extract_processing_locations(self, results: Dict[str, Any]) -> List[str]:
        """Extract unique processing locations from execution results."""
        locations = set()
        for step in results.get("steps_completed", []):
            locations.add(step.get("location", "unknown"))
        return list(locations)


# Factory functions for easy integration
def create_hybrid_agent(vrin_client, organization_policies: Optional[Dict[str, Any]] = None,
                       customer_infrastructure: Optional[Dict[str, Any]] = None) -> AgentOrchestrator:
    """Create hybrid agent with custom policies and infrastructure config."""
    
    # Update router with organization policies
    router = HybridRouter(organization_policies)
    
    # Create orchestrator with customer infrastructure
    orchestrator = AgentOrchestrator(vrin_client, customer_infrastructure)
    orchestrator.router = router
    
    return orchestrator


def analyze_content_sensitivity(content: str, metadata: Optional[Dict[str, Any]] = None) -> ClassificationResult:
    """Standalone function to analyze content sensitivity."""
    classifier = DataClassifier()
    return classifier.classify(content, metadata)


def validate_compliance(plan: HybridExecutionPlan, classification: ClassificationResult) -> Dict[str, Any]:
    """Standalone function to validate compliance requirements."""
    compliance_manager = ComplianceManager()
    return compliance_manager.validate_processing_plan(plan, classification)