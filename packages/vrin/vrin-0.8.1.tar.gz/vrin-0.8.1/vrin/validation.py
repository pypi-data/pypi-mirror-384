"""
Configuration validation and testing tools for VRIN enterprise deployments.

Validates configurations across different deployment modes and cloud providers.
"""

import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from .config import VRINConfig, DeploymentMode, DatabaseProvider, LLMProvider
from .providers.factory import ProviderFactory

logger = logging.getLogger(__name__)


class ValidationSeverity(Enum):
    """Validation issue severity levels."""
    ERROR = "error"         # Configuration invalid, will not work
    WARNING = "warning"     # Configuration may have issues
    INFO = "info"          # Informational message
    

@dataclass
class ValidationIssue:
    """Validation issue details."""
    severity: ValidationSeverity
    component: str
    message: str
    suggestion: Optional[str] = None
    

class ConfigValidator:
    """Validates VRIN configurations."""
    
    def __init__(self):
        """Initialize validator."""
        self.issues: List[ValidationIssue] = []
        
    def validate_config(self, config: VRINConfig) -> Tuple[bool, List[ValidationIssue]]:
        """Validate complete configuration."""
        self.issues = []
        
        # Validate deployment mode consistency
        self._validate_deployment_mode(config)
        
        # Validate database configuration
        self._validate_database_config(config)
        
        # Validate LLM configuration  
        self._validate_llm_config(config)
        
        # Validate network configuration (for hybrid/distributed)
        if config.deployment_mode != DeploymentMode.CENTRALIZED:
            self._validate_network_config(config)
            
        # Validate security configuration
        self._validate_security_config(config)
        
        # Cross-component validation
        self._validate_cross_component(config)
        
        # Check for errors
        has_errors = any(issue.severity == ValidationSeverity.ERROR for issue in self.issues)
        
        return not has_errors, self.issues
        
    def _validate_deployment_mode(self, config: VRINConfig):
        """Validate deployment mode configuration."""
        if config.deployment_mode == DeploymentMode.CENTRALIZED:
            # Centralized must use VRIN-controlled services
            if config.database.provider != DatabaseProvider.NEPTUNE:
                self._add_issue(
                    ValidationSeverity.WARNING,
                    "deployment_mode",
                    "Centralized mode typically uses Neptune database",
                    "Consider using Neptune for centralized deployment"
                )
                
            if config.network or config.organization_id:
                self._add_issue(
                    ValidationSeverity.INFO,
                    "deployment_mode", 
                    "Centralized mode doesn't require network or organization configuration",
                    "Remove network/organization config for centralized mode"
                )
                
        elif config.deployment_mode in [DeploymentMode.HYBRID, DeploymentMode.DISTRIBUTED]:
            # Enterprise modes require organization
            if not config.organization_id:
                self._add_issue(
                    ValidationSeverity.WARNING,
                    "deployment_mode",
                    "Enterprise deployment modes should specify organization_id"
                )
                
    def _validate_database_config(self, config: VRINConfig):
        """Validate database configuration."""
        db_config = config.database
        
        if not db_config.endpoint:
            self._add_issue(
                ValidationSeverity.ERROR,
                "database",
                "Database endpoint is required"
            )
            return
            
        # Provider-specific validation
        if db_config.provider == DatabaseProvider.NEPTUNE:
            self._validate_neptune_config(db_config)
            
        elif db_config.provider == DatabaseProvider.COSMOS_DB:
            self._validate_cosmos_db_config(db_config)
            
        elif db_config.provider == DatabaseProvider.JANUSGRAPH:
            self._validate_janusgraph_config(db_config)
            
    def _validate_neptune_config(self, db_config):
        """Validate Neptune-specific configuration."""
        if not db_config.endpoint.endswith('.neptune.amazonaws.com'):
            self._add_issue(
                ValidationSeverity.WARNING,
                "database",
                "Neptune endpoint should end with '.neptune.amazonaws.com'",
                "Verify Neptune cluster endpoint format"
            )
            
        if db_config.port and db_config.port != 8182:
            self._add_issue(
                ValidationSeverity.WARNING,
                "database",
                "Neptune typically uses port 8182",
                "Verify Neptune port configuration"
            )
            
        if db_config.region and db_config.region not in ['us-east-1', 'us-west-2', 'eu-west-1', 'ap-southeast-1']:
            self._add_issue(
                ValidationSeverity.INFO,
                "database",
                f"Neptune region {db_config.region} may have limited feature availability"
            )
            
    def _validate_cosmos_db_config(self, db_config):
        """Validate Cosmos DB configuration."""
        if not db_config.endpoint.endswith('.gremlin.cosmos.azure.com'):
            self._add_issue(
                ValidationSeverity.WARNING,
                "database",
                "Cosmos DB Gremlin endpoint should end with '.gremlin.cosmos.azure.com'",
                "Verify Cosmos DB Gremlin API endpoint"
            )
            
        if db_config.port and db_config.port != 443:
            self._add_issue(
                ValidationSeverity.WARNING,
                "database",
                "Cosmos DB Gremlin API typically uses port 443"
            )
            
        if not db_config.credentials or not db_config.credentials.get('account_key'):
            self._add_issue(
                ValidationSeverity.ERROR,
                "database",
                "Cosmos DB requires account_key in credentials"
            )
            
    def _validate_janusgraph_config(self, db_config):
        """Validate JanusGraph configuration.""" 
        if db_config.port and db_config.port not in [8182, 8183, 8184]:
            self._add_issue(
                ValidationSeverity.INFO,
                "database",
                f"JanusGraph port {db_config.port} is non-standard",
                "JanusGraph typically uses ports 8182-8184"
            )
            
        if db_config.additional_params:
            storage_backend = db_config.additional_params.get('storage_backend', 'berkeleyje')
            index_backend = db_config.additional_params.get('index_backend', 'elasticsearch')
            
            if storage_backend not in ['berkeleyje', 'cassandra', 'hbase', 'bigtable']:
                self._add_issue(
                    ValidationSeverity.WARNING,
                    "database",
                    f"Unsupported JanusGraph storage backend: {storage_backend}",
                    "Use berkeleyje, cassandra, hbase, or bigtable"
                )
                
    def _validate_llm_config(self, config: VRINConfig):
        """Validate LLM configuration."""
        llm_config = config.llm
        
        if not llm_config.api_key:
            self._add_issue(
                ValidationSeverity.ERROR,
                "llm",
                "LLM API key is required"
            )
            
        # Provider-specific validation
        if llm_config.provider == LLMProvider.OPENAI:
            self._validate_openai_config(llm_config)
            
        elif llm_config.provider == LLMProvider.AZURE_OPENAI:
            self._validate_azure_openai_config(llm_config)
            
    def _validate_openai_config(self, llm_config):
        """Validate OpenAI configuration."""
        valid_models = ['gpt-4', 'gpt-4o', 'gpt-4o-mini', 'gpt-3.5-turbo']
        
        if llm_config.model not in valid_models:
            self._add_issue(
                ValidationSeverity.WARNING,
                "llm",
                f"Model {llm_config.model} may not be supported",
                f"Recommended models: {', '.join(valid_models)}"
            )
            
        if llm_config.temperature < 0 or llm_config.temperature > 2:
            self._add_issue(
                ValidationSeverity.WARNING,
                "llm",
                "Temperature should be between 0 and 2",
                "Use 0.0-0.3 for factual extraction, 0.3-1.0 for creative tasks"
            )
            
    def _validate_azure_openai_config(self, llm_config):
        """Validate Azure OpenAI configuration."""
        if not llm_config.endpoint:
            self._add_issue(
                ValidationSeverity.ERROR,
                "llm",
                "Azure OpenAI endpoint is required"
            )
            return
            
        if not llm_config.endpoint.endswith('.openai.azure.com'):
            self._add_issue(
                ValidationSeverity.WARNING,
                "llm",
                "Azure OpenAI endpoint should end with '.openai.azure.com'"
            )
            
        if not llm_config.additional_params or not llm_config.additional_params.get('deployment_name'):
            self._add_issue(
                ValidationSeverity.ERROR,
                "llm",
                "Azure OpenAI requires deployment_name in additional_params"
            )
            
    def _validate_network_config(self, config: VRINConfig):
        """Validate network configuration for hybrid deployments."""
        if not config.network:
            self._add_issue(
                ValidationSeverity.WARNING,
                "network",
                "Hybrid/distributed deployments should specify network configuration",
                "Add VPC, subnet, and security group configuration"
            )
            return
            
        network = config.network
        
        # VPC validation
        if network.vpc_id and not network.vpc_id.startswith('vpc-'):
            self._add_issue(
                ValidationSeverity.WARNING,
                "network",
                "VPC ID should start with 'vpc-'",
                "Verify AWS VPC ID format"
            )
            
        # Subnet validation  
        if network.subnet_ids:
            for subnet_id in network.subnet_ids:
                if not subnet_id.startswith('subnet-'):
                    self._add_issue(
                        ValidationSeverity.WARNING,
                        "network",
                        f"Subnet ID {subnet_id} should start with 'subnet-'",
                        "Verify AWS subnet ID format"
                    )
                    
        # Connectivity validation
        connectivity_count = sum([
            bool(network.private_link_endpoint),
            bool(network.vpn_connection),
            bool(network.direct_connect)
        ])
        
        if connectivity_count == 0:
            self._add_issue(
                ValidationSeverity.WARNING,
                "network", 
                "No connectivity method specified",
                "Consider Private Link, VPN, or Direct Connect"
            )
        elif connectivity_count > 1:
            self._add_issue(
                ValidationSeverity.INFO,
                "network",
                "Multiple connectivity methods configured",
                "Ensure routing is configured correctly"
            )
            
    def _validate_security_config(self, config: VRINConfig):
        """Validate security configuration."""
        if not config.security:
            self._add_issue(
                ValidationSeverity.INFO,
                "security",
                "No security configuration specified",
                "Consider adding encryption and compliance settings"
            )
            return
            
        security = config.security
        
        # Encryption validation
        if not security.encryption_at_rest:
            self._add_issue(
                ValidationSeverity.WARNING,
                "security",
                "Encryption at rest is disabled",
                "Enable encryption for production deployments"
            )
            
        if not security.encryption_in_transit:
            self._add_issue(
                ValidationSeverity.WARNING,
                "security",
                "Encryption in transit is disabled", 
                "Enable TLS/SSL for production deployments"
            )
            
        # Compliance validation
        if security.compliance_standards:
            valid_standards = ['SOC2', 'HIPAA', 'GDPR', 'PCI-DSS', 'FedRAMP']
            for standard in security.compliance_standards:
                if standard not in valid_standards:
                    self._add_issue(
                        ValidationSeverity.INFO,
                        "security",
                        f"Compliance standard {standard} may require additional configuration"
                    )
                    
    def _validate_cross_component(self, config: VRINConfig):
        """Validate cross-component compatibility."""
        # Database + LLM provider combinations
        if (config.database.provider == DatabaseProvider.COSMOS_DB and 
            config.llm.provider != LLMProvider.AZURE_OPENAI):
            self._add_issue(
                ValidationSeverity.INFO,
                "compatibility",
                "Cosmos DB + non-Azure LLM may have higher latency",
                "Consider Azure OpenAI for optimal performance"
            )
            
        # Deployment mode + configuration consistency
        if (config.deployment_mode == DeploymentMode.CENTRALIZED and
            config.database.provider != DatabaseProvider.NEPTUNE):
            self._add_issue(
                ValidationSeverity.WARNING,
                "compatibility", 
                "Centralized mode with non-Neptune database is unusual",
                "Verify this is the intended configuration"
            )
            
        # Region consistency
        db_region = config.database.region
        security_region = config.security.data_residency_region if config.security else None
        
        if db_region and security_region and db_region != security_region:
            self._add_issue(
                ValidationSeverity.WARNING,
                "compatibility",
                "Database region and data residency region don't match",
                "Ensure compliance with data residency requirements"
            )
            
    def _add_issue(self, severity: ValidationSeverity, component: str, message: str, suggestion: str = None):
        """Add validation issue."""
        issue = ValidationIssue(
            severity=severity,
            component=component,
            message=message,
            suggestion=suggestion
        )
        self.issues.append(issue)


class ConfigTester:
    """Tests VRIN configurations by attempting connections."""
    
    def __init__(self):
        """Initialize config tester."""
        self.test_results: Dict[str, Any] = {}
        
    def test_config(self, config: VRINConfig, skip_llm: bool = False) -> Dict[str, Any]:
        """Test configuration by connecting to providers."""
        self.test_results = {
            'overall': {'status': 'unknown'},
            'database': {'status': 'not_tested'},
            'llm': {'status': 'not_tested'},
            'timestamp': None
        }
        
        import time
        start_time = time.time()
        
        try:
            # Test using provider factory
            results = ProviderFactory.test_providers(config)
            self.test_results.update(results)
            
            # Add timing information
            self.test_results['test_duration'] = f"{time.time() - start_time:.2f}s"
            self.test_results['timestamp'] = int(time.time())
            
            return self.test_results
            
        except Exception as e:
            logger.error(f"Config testing failed: {str(e)}")
            
            self.test_results.update({
                'overall': {'status': 'error', 'error': str(e)},
                'test_duration': f"{time.time() - start_time:.2f}s",
                'timestamp': int(time.time())
            })
            
            return self.test_results
            
    def generate_test_report(self) -> Dict[str, Any]:
        """Generate detailed test report."""
        if not self.test_results:
            return {'error': 'No test results available'}
            
        report = {
            'summary': {
                'overall_status': self.test_results.get('overall', {}).get('status', 'unknown'),
                'database_status': self.test_results.get('database', {}).get('status', 'unknown'),
                'llm_status': self.test_results.get('llm', {}).get('status', 'unknown'),
                'test_duration': self.test_results.get('test_duration'),
                'timestamp': self.test_results.get('timestamp')
            },
            'details': {
                'database': self.test_results.get('database', {}),
                'llm': self.test_results.get('llm', {}),
                'overall': self.test_results.get('overall', {})
            },
            'recommendations': self._generate_recommendations()
        }
        
        return report
        
    def _generate_recommendations(self) -> List[str]:
        """Generate recommendations based on test results."""
        recommendations = []
        
        db_status = self.test_results.get('database', {}).get('status')
        llm_status = self.test_results.get('llm', {}).get('status')
        
        if db_status == 'unhealthy':
            recommendations.append("Check database endpoint, credentials, and network connectivity")
            
        if llm_status == 'unhealthy':
            recommendations.append("Verify LLM API key and endpoint configuration")
            
        if db_status == 'healthy' and llm_status == 'healthy':
            recommendations.append("Configuration is working correctly")
            
        return recommendations


def validate_and_test_config(config: VRINConfig) -> Dict[str, Any]:
    """Validate and test configuration in one operation."""
    # Validation
    validator = ConfigValidator()
    is_valid, issues = validator.validate_config(config)
    
    # Testing (only if validation passes)
    test_results = {}
    if is_valid:
        tester = ConfigTester()
        test_results = tester.test_config(config)
        
    return {
        'validation': {
            'is_valid': is_valid,
            'issues': [
                {
                    'severity': issue.severity.value,
                    'component': issue.component,
                    'message': issue.message,
                    'suggestion': issue.suggestion
                }
                for issue in issues
            ]
        },
        'testing': test_results,
        'overall_status': 'ready' if is_valid and test_results.get('overall', {}).get('status') == 'healthy' else 'not_ready'
    }