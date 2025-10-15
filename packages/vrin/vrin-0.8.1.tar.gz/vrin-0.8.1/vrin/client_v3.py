"""
VRIN Client v3 - Hybrid Agent Integration

Enhanced client that supports hybrid processing with intelligent routing
based on data sensitivity and compliance requirements.

Features:
- Automatic data classification
- Intelligent routing to private/cloud infrastructure
- Compliance-aware processing
- Hybrid execution orchestration
- Enterprise security controls
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

from .client_v2 import VRINClient, create_vpc_isolated_client
from .agents import (
    AgentOrchestrator, DataClassifier, HybridRouter, ComplianceManager,
    ClassificationResult, RoutingDecision, HybridExecutionPlan,
    SensitivityLevel, ProcessingLocation, ComplianceRegime
)

logger = logging.getLogger(__name__)


class HybridVRINClient(VRINClient):
    """Enhanced VRIN client with hybrid processing capabilities."""
    
    def __init__(self, api_key: str, base_url: str = None, auth_base_url: str = None,
                 organization_policies: Optional[Dict[str, Any]] = None,
                 customer_infrastructure: Optional[Dict[str, Any]] = None,
                 enable_hybrid: bool = True):
        """
        Initialize hybrid VRIN client.
        
        Args:
            api_key: VRIN API key
            base_url: VRIN RAG API base URL  
            auth_base_url: VRIN Auth API base URL
            organization_policies: Custom routing and security policies
            customer_infrastructure: Customer's private infrastructure config
            enable_hybrid: Enable hybrid processing (default: True)
        """
        super().__init__(api_key, base_url, auth_base_url)
        
        self.enable_hybrid = enable_hybrid
        self.organization_policies = organization_policies or {}
        self.customer_infrastructure = customer_infrastructure or {}
        
        # Initialize hybrid components
        if self.enable_hybrid:
            self.agent_orchestrator = AgentOrchestrator(
                vrin_client=self,
                customer_infrastructure_config=customer_infrastructure
            )
            self.data_classifier = DataClassifier()
            self.hybrid_router = HybridRouter(organization_policies)
            self.compliance_manager = ComplianceManager()
        
        logger.info(f"HybridVRINClient initialized with hybrid processing: {enable_hybrid}")
    
    def insert_with_classification(self, content: str, title: str = None,
                                 metadata: Optional[Dict[str, Any]] = None,
                                 classification_override: Optional[ClassificationResult] = None) -> Dict[str, Any]:
        """
        Insert content with automatic data classification and hybrid processing.
        
        Args:
            content: Content to insert
            title: Optional title
            metadata: Additional metadata for classification
            classification_override: Override automatic classification
            
        Returns:
            Dict containing insertion results and processing details
        """
        
        if not self.enable_hybrid:
            # Fallback to standard processing
            return self.insert(content=content, title=title)
        
        try:
            start_time = datetime.now()
            
            # Step 1: Classify data sensitivity
            if classification_override:
                classification = classification_override
            else:
                classification = self.data_classifier.classify(content, metadata)
            
            logger.info(f"Content classified as {classification.sensitivity_level.value} "
                       f"with {classification.confidence:.2f} confidence")
            
            # Step 2: Create execution plan
            execution_plan = self.agent_orchestrator.create_execution_plan(
                content=content,
                user_id=self._get_user_id(),
                metadata=metadata
            )
            
            # Step 3: Validate compliance
            compliance_validation = self.compliance_manager.validate_processing_plan(
                execution_plan, classification
            )
            
            if not compliance_validation["compliant"]:
                logger.warning(f"Compliance violations detected: {compliance_validation['violations']}")
                # Could either fail here or adjust the plan
            
            # Step 4: Execute hybrid processing
            execution_results = self.agent_orchestrator.execute_plan(execution_plan)
            
            # Step 5: Generate compliance report
            compliance_report = self.compliance_manager.generate_compliance_report(execution_results)
            
            end_time = datetime.now()
            processing_duration = (end_time - start_time).total_seconds()
            
            return {
                "status": "completed",
                "processing_type": "hybrid",
                "classification": {
                    "sensitivity_level": classification.sensitivity_level.value,
                    "confidence": classification.confidence,
                    "detected_entities": classification.detected_entities,
                    "compliance_requirements": [r.value for r in classification.compliance_requirements]
                },
                "routing_decision": {
                    "processing_location": execution_plan.routing_decision.processing_location.value,
                    "reasoning": execution_plan.routing_decision.reasoning
                },
                "execution_results": execution_results,
                "compliance_report": compliance_report,
                "processing_duration_seconds": processing_duration,
                "security_controls_applied": execution_plan.security_controls
            }
            
        except Exception as e:
            logger.error(f"Hybrid processing failed: {str(e)}")
            
            # Graceful fallback to standard processing
            logger.info("Falling back to standard VRIN processing")
            fallback_result = self.insert(content=content, title=title)
            fallback_result["processing_type"] = "fallback_standard"
            fallback_result["hybrid_error"] = str(e)
            return fallback_result
    
    def query_with_routing(self, question: str, 
                          sensitivity_context: Optional[SensitivityLevel] = None,
                          force_location: Optional[ProcessingLocation] = None) -> Dict[str, Any]:
        """
        Query with intelligent routing based on question sensitivity.
        
        Args:
            question: Question to ask
            sensitivity_context: Override sensitivity level for routing
            force_location: Force processing at specific location
            
        Returns:
            Dict containing query results and processing details
        """
        
        if not self.enable_hybrid:
            # Fallback to standard processing
            return self.query(question)
        
        try:
            # Classify the question for sensitivity
            question_classification = self.data_classifier.classify(question)
            
            if sensitivity_context:
                question_classification.sensitivity_level = sensitivity_context
            
            # Make routing decision for query processing
            available_infra = {
                "customer_private": bool(self.customer_infrastructure.get("neptune_endpoint")),
                "vrin_cloud": True
            }
            
            routing_decision = self.hybrid_router.route(question_classification, available_infra)
            
            if force_location:
                routing_decision.query_processing_location = force_location
            
            # Execute query based on routing decision
            if routing_decision.query_processing_location == ProcessingLocation.CUSTOMER_PRIVATE:
                query_result = self._execute_private_query(question)
            else:
                query_result = self.query(question)  # Standard VRIN cloud query
            
            return {
                "answer": query_result.get("answer", ""),
                "sources": query_result.get("sources", []),
                "processing_type": "hybrid_routed",
                "query_classification": {
                    "sensitivity_level": question_classification.sensitivity_level.value,
                    "confidence": question_classification.confidence
                },
                "processing_location": routing_decision.query_processing_location.value,
                "routing_reasoning": routing_decision.reasoning,
                "security_controls": routing_decision.compliance_controls
            }
            
        except Exception as e:
            logger.error(f"Hybrid query routing failed: {str(e)}")
            
            # Graceful fallback
            fallback_result = self.query(question)
            if isinstance(fallback_result, dict):
                fallback_result["processing_type"] = "fallback_standard" 
                fallback_result["hybrid_error"] = str(e)
            else:
                fallback_result = {
                    "answer": str(fallback_result),
                    "processing_type": "fallback_standard",
                    "hybrid_error": str(e)
                }
            return fallback_result
    
    def get_hybrid_analytics(self) -> Dict[str, Any]:
        """Get analytics on hybrid processing patterns and performance."""
        
        if not self.enable_hybrid:
            return {"error": "Hybrid processing not enabled"}
        
        # This would typically query stored metrics
        # For now, return simulated analytics
        return {
            "hybrid_processing_enabled": True,
            "data_classification_stats": {
                "public": 20,
                "internal": 45, 
                "confidential": 30,
                "highly_sensitive": 5
            },
            "routing_decisions": {
                "vrin_cloud": 65,
                "customer_private": 25,
                "hybrid": 10
            },
            "compliance_regimes": {
                "gdpr": 15,
                "hipaa": 8,
                "sox": 12,
                "pci_dss": 3,
                "none": 62
            },
            "average_processing_times": {
                "vrin_cloud": 8.5,
                "customer_private": 12.3,
                "hybrid": 15.7
            },
            "security_controls_usage": {
                "end_to_end_encryption": 30,
                "private_network_only": 25,
                "audit_logging": 80,
                "data_anonymization": 15
            }
        }
    
    def configure_organization_policies(self, policies: Dict[str, Any]) -> Dict[str, Any]:
        """Update organization policies for hybrid processing."""
        
        self.organization_policies.update(policies)
        
        # Recreate hybrid router with new policies
        if self.enable_hybrid:
            self.hybrid_router = HybridRouter(self.organization_policies)
            self.agent_orchestrator.router = self.hybrid_router
        
        return {
            "status": "updated",
            "active_policies": self.organization_policies
        }
    
    def validate_customer_infrastructure(self) -> Dict[str, Any]:
        """Validate customer's private infrastructure configuration."""
        
        validation_result = {
            "valid": True,
            "checks": [],
            "recommendations": []
        }
        
        # Check Neptune endpoint
        if self.customer_infrastructure.get("neptune_endpoint"):
            validation_result["checks"].append({
                "component": "Neptune Database",
                "status": "configured",
                "endpoint": self.customer_infrastructure["neptune_endpoint"]
            })
        else:
            validation_result["valid"] = False
            validation_result["checks"].append({
                "component": "Neptune Database", 
                "status": "missing",
                "recommendation": "Configure Neptune endpoint for private graph storage"
            })
        
        # Check OpenSearch endpoint
        if self.customer_infrastructure.get("opensearch_endpoint"):
            validation_result["checks"].append({
                "component": "OpenSearch Domain",
                "status": "configured",
                "endpoint": self.customer_infrastructure["opensearch_endpoint"]
            })
        else:
            validation_result["recommendations"].append(
                "Consider configuring OpenSearch for private vector storage"
            )
        
        # Check VPC configuration
        if self.customer_infrastructure.get("vpc_id"):
            validation_result["checks"].append({
                "component": "VPC Isolation",
                "status": "configured",
                "vpc_id": self.customer_infrastructure["vpc_id"]
            })
        else:
            validation_result["recommendations"].append(
                "Configure VPC isolation for enhanced security"
            )
        
        return validation_result
    
    def _execute_private_query(self, question: str) -> Dict[str, Any]:
        """Execute query on customer's private infrastructure."""
        
        # In production, this would connect to customer's Neptune/OpenSearch
        # For now, simulate private query execution
        
        return {
            "answer": f"Private infrastructure response to: {question}",
            "sources": ["Private Customer Database"],
            "processing_location": "customer_private",
            "security_level": "maximum"
        }
    
    def _get_user_id(self) -> str:
        """Get current user ID for processing."""
        # This would typically extract from JWT token or session
        return "hybrid_user_" + str(hash(self.api_key))[:8]


# Factory functions for different hybrid configurations

def create_hybrid_enterprise_client(
    api_key: str,
    neptune_endpoint: str,
    openai_api_key: str,
    organization_policies: Optional[Dict[str, Any]] = None,
    vpc_config: Optional[Dict[str, Any]] = None
) -> HybridVRINClient:
    """
    Create hybrid client for enterprise deployment with private Neptune.
    
    Args:
        api_key: VRIN API key
        neptune_endpoint: Customer's Neptune cluster endpoint
        openai_api_key: OpenAI API key for LLM processing
        organization_policies: Custom security and routing policies
        vpc_config: VPC configuration for network isolation
    """
    
    customer_infrastructure = {
        "neptune_endpoint": neptune_endpoint,
        "openai_api_key": openai_api_key
    }
    
    if vpc_config:
        customer_infrastructure.update(vpc_config)
    
    return HybridVRINClient(
        api_key=api_key,
        organization_policies=organization_policies,
        customer_infrastructure=customer_infrastructure,
        enable_hybrid=True
    )


def create_compliance_aware_client(
    api_key: str,
    compliance_regimes: List[ComplianceRegime],
    customer_infrastructure: Optional[Dict[str, Any]] = None
) -> HybridVRINClient:
    """
    Create client optimized for specific compliance requirements.
    
    Args:
        api_key: VRIN API key
        compliance_regimes: List of compliance frameworks to enforce
        customer_infrastructure: Customer's private infrastructure config
    """
    
    # Create policies based on compliance requirements
    organization_policies = {
        "compliance_override": True,
        "force_private": any(regime in [ComplianceRegime.HIPAA, ComplianceRegime.PCI_DSS] 
                           for regime in compliance_regimes)
    }
    
    return HybridVRINClient(
        api_key=api_key,
        organization_policies=organization_policies,
        customer_infrastructure=customer_infrastructure or {},
        enable_hybrid=True
    )


def create_performance_optimized_client(
    api_key: str,
    customer_infrastructure: Optional[Dict[str, Any]] = None
) -> HybridVRINClient:
    """
    Create client optimized for performance over security.
    
    Args:
        api_key: VRIN API key
        customer_infrastructure: Customer's private infrastructure config
    """
    
    organization_policies = {
        "performance_priority": True,
        "cost_optimization": True,
        "compliance_override": False
    }
    
    return HybridVRINClient(
        api_key=api_key,
        organization_policies=organization_policies,
        customer_infrastructure=customer_infrastructure or {},
        enable_hybrid=True
    )