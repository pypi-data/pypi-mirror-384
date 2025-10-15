"""
VRIN Enterprise Client - Extended client for enterprise customers with private infrastructure
"""

import requests
import json
import time
import socket
import ssl
from typing import Dict, List, Any, Optional, Tuple
from .client import VRINClient
from .exceptions import VRINError

class VRINEnterpriseClient(VRINClient):
    """VRIN Enterprise Client with private infrastructure support"""
    
    def __init__(self, api_key: str, **kwargs):
        """
        Initialize VRIN Enterprise client
        
        Args:
            api_key: Enterprise API key (format: vrin_ent_XXXXXX)
            **kwargs: Optional enterprise configuration overrides
        """
        
        # Validate enterprise API key format
        if not api_key.startswith('vrin_ent_'):
            raise ValueError("Enterprise API key must start with 'vrin_ent_'")
        
        # Initialize base client
        super().__init__(api_key)
        
        # Enterprise-specific URLs
        self.enterprise_base_url = "https://thuiu23t0c.execute-api.us-east-1.amazonaws.com/dev"  # Will be updated with enterprise endpoints
        
        # Check if enterprise configuration is provided directly
        self.organization_id = kwargs.get('organization_id')
        self.deployment_mode = kwargs.get('deployment_mode', 'vpc_isolated')
        self.private_endpoints = kwargs.get('private_endpoints', {})
        
        # Enterprise configuration (will be loaded from backend)
        self.configuration = None
        self.organization_context = None
        
        # Load enterprise configuration from backend
        self._load_enterprise_configuration()
        
        # Validation checkpoints
        self.validation_results = {
            'configuration_loaded': False,
            'endpoints_validated': False,
            'database_connectivity': None,
            'vector_store_connectivity': None,
            'llm_provider_connectivity': None,
            'last_validation': None
        }
    
    def _load_enterprise_configuration(self):
        """Load enterprise configuration from VRIN backend"""
        
        try:
            # For now, we'll authenticate with the standard endpoint
            # In production, this would call the enterprise portal API
            response = requests.post(
                f"{self.enterprise_base_url}/enterprise/authenticate",
                headers=self.headers,
                json={'api_key': self.api_key},
                timeout=30
            )
            
            if response.status_code == 200:
                auth_data = response.json()
                if auth_data.get('success'):
                    self.organization_context = {
                        'organization_id': auth_data.get('organization_id'),
                        'permissions': auth_data.get('permissions', []),
                        'rate_limits': auth_data.get('rate_limits', {}),
                    }
                    self.configuration = auth_data.get('configuration')
                    
                    # Update endpoints if configuration provides private endpoints
                    if self.configuration and 'private_endpoints' in self.configuration:
                        self._update_private_endpoints(self.configuration['private_endpoints'])
        
        except Exception as e:
            # Fallback to standard endpoints if enterprise authentication fails
            print(f"Warning: Could not load enterprise configuration: {str(e)}")
            print("Falling back to standard VRIN endpoints")
    
    def _update_private_endpoints(self, private_endpoints: Dict[str, str]):
        """Update client to use private enterprise endpoints"""
        
        if 'rag_api' in private_endpoints:
            self.rag_base_url = private_endpoints['rag_api']
        
        if 'auth_api' in private_endpoints:
            self.auth_base_url = private_endpoints['auth_api']
    
    def _make_enterprise_request(self, endpoint: str, method: str = 'POST', data: Dict = None) -> Dict[str, Any]:
        """Make request with enterprise context and private endpoint routing"""
        
        # Add enterprise context to all requests
        if data is None:
            data = {}
        
        if self.organization_context:
            data['_enterprise_context'] = {
                'organization_id': self.organization_context['organization_id'],
                'deployment_mode': self.deployment_mode
            }
        
        # Use appropriate HTTP method
        if method == 'GET':
            response = requests.get(endpoint, headers=self.headers, params=data, timeout=60)
        else:
            response = requests.post(endpoint, headers=self.headers, json=data, timeout=60)
        
        return response
    
    def insert(self, content: str, title: str = None, tags: List[str] = None, 
               processing_location: str = 'auto') -> Dict[str, Any]:
        """
        Insert content with enterprise processing location control
        
        Args:
            content: Content to insert
            title: Optional title
            tags: Optional tags
            processing_location: 'auto', 'private', or 'public' (client-controlled routing)
        """
        
        try:
            payload = {
                'content': content,
                'title': title or 'Untitled',
                'tags': tags or [],
                'processing_location': processing_location  # Enterprise feature
            }
            
            # Use enterprise request method
            response = self._make_enterprise_request(
                f"{self.rag_base_url}/insert",
                method='POST',
                data=payload
            )
            
            if response.status_code == 200:
                result = response.json()
                return {
                    'success': result.get('success', True),
                    'chunk_id': result.get('chunk_id'),
                    'facts_extracted': result.get('facts_count', result.get('facts_extracted', 0)),
                    'facts': result.get('facts', []),
                    'processing_location': result.get('processing_location', 'unknown'),
                    'storage_optimization': result.get('storage_optimization'),
                    'message': result.get('message', 'Content processed successfully'),
                    'enterprise_metadata': {
                        'organization_id': self.organization_context.get('organization_id') if self.organization_context else None,
                        'deployment_mode': self.deployment_mode,
                        'data_residency': result.get('data_residency', 'private')
                    }
                }
            else:
                return {
                    'success': False,
                    'error': f"HTTP {response.status_code}: {response.text}"
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f"Request failed: {str(e)}"
            }
    
    def query(self, query: str, processing_location: str = 'auto', 
              use_enterprise_specialization: bool = True) -> Dict[str, Any]:
        """
        Query with enterprise specialization and processing location control
        
        Args:
            query: Query string
            processing_location: 'auto', 'private', or 'public'
            use_enterprise_specialization: Use organization's custom specialization
        """
        
        try:
            payload = {
                'query': query,
                'processing_location': processing_location,
                'use_enterprise_specialization': use_enterprise_specialization
            }
            
            response = self._make_enterprise_request(
                f"{self.rag_base_url}/query",
                method='POST',
                data=payload
            )
            
            if response.status_code == 200:
                result = response.json()
                
                # Add enterprise-specific metadata
                enterprise_metadata = {
                    'organization_id': self.organization_context.get('organization_id') if self.organization_context else None,
                    'deployment_mode': self.deployment_mode,
                    'processing_location': result.get('processing_location', 'private'),
                    'data_residency': result.get('data_residency', 'private'),
                    'specialization_applied': result.get('specialization_applied', False)
                }
                
                return {
                    **result,
                    'enterprise_metadata': enterprise_metadata
                }
            else:
                return {
                    'success': False,
                    'error': f"HTTP {response.status_code}: {response.text}"
                }
        
        except Exception as e:
            return {
                'success': False,
                'error': f"Request failed: {str(e)}"
            }
    
    def get_organization_info(self) -> Dict[str, Any]:
        """Get organization information and configuration status"""
        
        if not self.organization_context:
            return {
                'success': False,
                'error': 'No organization context available'
            }
        
        return {
            'success': True,
            'organization_id': self.organization_context['organization_id'],
            'deployment_mode': self.deployment_mode,
            'permissions': self.organization_context['permissions'],
            'rate_limits': self.organization_context['rate_limits'],
            'configuration_status': 'active' if self.configuration else 'not_configured',
            'private_endpoints_configured': bool(self.configuration and 'private_endpoints' in self.configuration)
        }
    
    def update_specialization(self, specialization_config: Dict[str, Any]) -> Dict[str, Any]:
        """Update enterprise specialization configuration"""
        
        if not self.organization_context:
            return {
                'success': False,
                'error': 'No organization context available'
            }
        
        try:
            payload = {
                'organization_id': self.organization_context['organization_id'],
                'specialization_config': specialization_config
            }
            
            response = self._make_enterprise_request(
                f"{self.enterprise_base_url}/enterprise/specialization",
                method='POST',
                data=payload
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {
                    'success': False,
                    'error': f"Failed to update specialization: {response.status_code}"
                }
        
        except Exception as e:
            return {
                'success': False,
                'error': f"Request failed: {str(e)}"
            }
    
    def validate_enterprise_configuration(self) -> Dict[str, Any]:
        """
        Comprehensive validation of enterprise configuration and connectivity
        Returns detailed validation report with specific error messages
        """
        
        validation_report = {
            'overall_status': 'unknown',
            'checkpoints': {},
            'errors': [],
            'warnings': [],
            'recommendations': [],
            'timestamp': int(time.time())
        }
        
        print("🔍 Running Enterprise Configuration Validation...")
        
        # Checkpoint 1: Configuration Loading
        checkpoint_1 = self._validate_configuration_loading()
        validation_report['checkpoints']['configuration_loading'] = checkpoint_1
        
        if not checkpoint_1['passed']:
            validation_report['errors'].extend(checkpoint_1['errors'])
            validation_report['overall_status'] = 'failed'
            return validation_report
        
        # Checkpoint 2: Endpoint Validation
        checkpoint_2 = self._validate_endpoints()
        validation_report['checkpoints']['endpoint_validation'] = checkpoint_2
        
        if not checkpoint_2['passed']:
            validation_report['errors'].extend(checkpoint_2['errors'])
            if validation_report['overall_status'] != 'failed':
                validation_report['overall_status'] = 'failed'
        
        # Checkpoint 3: Database Connectivity
        checkpoint_3 = self._validate_database_connectivity()
        validation_report['checkpoints']['database_connectivity'] = checkpoint_3
        
        if not checkpoint_3['passed']:
            validation_report['errors'].extend(checkpoint_3['errors'])
            if validation_report['overall_status'] != 'failed':
                validation_report['overall_status'] = 'partial'
        
        # Checkpoint 4: Vector Store Connectivity
        checkpoint_4 = self._validate_vector_store_connectivity()
        validation_report['checkpoints']['vector_store_connectivity'] = checkpoint_4
        
        if not checkpoint_4['passed']:
            validation_report['errors'].extend(checkpoint_4['errors'])
            if validation_report['overall_status'] != 'failed':
                validation_report['overall_status'] = 'partial'
        
        # Checkpoint 5: LLM Provider Connectivity
        checkpoint_5 = self._validate_llm_connectivity()
        validation_report['checkpoints']['llm_connectivity'] = checkpoint_5
        
        if not checkpoint_5['passed']:
            validation_report['errors'].extend(checkpoint_5['errors'])
            if validation_report['overall_status'] != 'failed':
                validation_report['overall_status'] = 'partial'
        
        # Checkpoint 6: End-to-End Functionality
        checkpoint_6 = self._validate_end_to_end_functionality()
        validation_report['checkpoints']['end_to_end_functionality'] = checkpoint_6
        
        if not checkpoint_6['passed']:
            validation_report['errors'].extend(checkpoint_6['errors'])
            if validation_report['overall_status'] != 'failed':
                validation_report['overall_status'] = 'partial'
        
        # Determine overall status
        if validation_report['overall_status'] == 'unknown':
            all_passed = all(cp['passed'] for cp in validation_report['checkpoints'].values())
            validation_report['overall_status'] = 'passed' if all_passed else 'partial'
        
        # Add recommendations
        validation_report['recommendations'] = self._generate_recommendations(validation_report)
        
        # Update internal validation state
        self.validation_results.update({
            'configuration_loaded': checkpoint_1['passed'],
            'endpoints_validated': checkpoint_2['passed'], 
            'database_connectivity': checkpoint_3['passed'],
            'vector_store_connectivity': checkpoint_4['passed'],
            'llm_provider_connectivity': checkpoint_5['passed'],
            'last_validation': validation_report['timestamp']
        })
        
        return validation_report
    
    def _validate_configuration_loading(self) -> Dict[str, Any]:
        """Validate enterprise configuration was loaded successfully"""
        
        checkpoint = {
            'name': 'Configuration Loading',
            'passed': False,
            'errors': [],
            'details': {}
        }
        
        try:
            # Check if organization context exists
            if not self.organization_context:
                checkpoint['errors'].append(
                    "❌ Enterprise configuration not loaded. Possible causes:\n"
                    "   • API key not found in enterprise database\n" 
                    "   • Organization not properly set up in VRIN portal\n"
                    "   • Network connectivity issues to VRIN backend"
                )
                return checkpoint
            
            # Check if configuration exists
            if not self.configuration:
                checkpoint['errors'].append(
                    "❌ Infrastructure configuration not found. Please:\n"
                    "   • Log into VRIN Enterprise Portal\n"
                    "   • Navigate to Infrastructure Configuration\n"
                    "   • Complete and save your infrastructure settings"
                )
                return checkpoint
            
            # Validate required configuration fields
            required_fields = {
                'infrastructure.database.endpoint': 'Database endpoint',
                'infrastructure.vector_store.endpoint': 'Vector store endpoint',
                'infrastructure.llm.provider': 'LLM provider'
            }
            
            missing_fields = []
            for field_path, field_name in required_fields.items():
                if not self._get_nested_config(field_path):
                    missing_fields.append(f"   • {field_name} ({field_path})")
            
            if missing_fields:
                checkpoint['errors'].append(
                    f"❌ Configuration incomplete. Missing required fields:\n" + 
                    "\n".join(missing_fields) +
                    "\n\n   Please complete your configuration in the VRIN Enterprise Portal"
                )
                return checkpoint
            
            checkpoint['passed'] = True
            checkpoint['details'] = {
                'organization_id': self.organization_context.get('organization_id'),
                'deployment_mode': self.configuration.get('deployment_mode'),
                'cloud_provider': self.configuration.get('cloud_provider')
            }
            
            return checkpoint
            
        except Exception as e:
            checkpoint['errors'].append(f"❌ Configuration validation failed: {str(e)}")
            return checkpoint
    
    def _validate_endpoints(self) -> Dict[str, Any]:
        """Validate all configured endpoints are accessible"""
        
        checkpoint = {
            'name': 'Endpoint Validation',
            'passed': False,
            'errors': [],
            'details': {}
        }
        
        try:
            endpoints_to_check = []
            
            # Database endpoint
            db_endpoint = self._get_nested_config('infrastructure.database.endpoint')
            if db_endpoint:
                db_port = self._get_nested_config('infrastructure.database.port', 8182)
                endpoints_to_check.append({
                    'name': 'Database (Neptune/Cosmos DB)',
                    'host': db_endpoint,
                    'port': db_port,
                    'type': 'database'
                })
            
            # Vector store endpoint
            vs_endpoint = self._get_nested_config('infrastructure.vector_store.endpoint')
            if vs_endpoint:
                # Extract host from URL
                host = vs_endpoint.replace('https://', '').replace('http://', '').split('/')[0]
                endpoints_to_check.append({
                    'name': 'Vector Store (OpenSearch/Elasticsearch)',
                    'host': host,
                    'port': 443,
                    'type': 'vector_store'
                })
            
            failed_endpoints = []
            successful_endpoints = []
            
            for endpoint in endpoints_to_check:
                result = self._check_endpoint_connectivity(
                    endpoint['host'], 
                    endpoint['port'], 
                    endpoint['name']
                )
                
                if result['success']:
                    successful_endpoints.append(endpoint['name'])
                    checkpoint['details'][endpoint['type']] = 'reachable'
                else:
                    failed_endpoints.append({
                        'name': endpoint['name'],
                        'error': result['error'],
                        'host': endpoint['host'],
                        'port': endpoint['port']
                    })
                    checkpoint['details'][endpoint['type']] = 'unreachable'
            
            if failed_endpoints:
                error_details = []
                for failed in failed_endpoints:
                    error_details.append(
                        f"   • {failed['name']}: {failed['host']}:{failed['port']}\n"
                        f"     Error: {failed['error']}\n"
                        f"     Check: Network connectivity, security groups, VPC configuration"
                    )
                
                checkpoint['errors'].append(
                    f"❌ Endpoint connectivity failed:\n" + "\n".join(error_details)
                )
            
            if successful_endpoints and not failed_endpoints:
                checkpoint['passed'] = True
            
            return checkpoint
            
        except Exception as e:
            checkpoint['errors'].append(f"❌ Endpoint validation failed: {str(e)}")
            return checkpoint
    
    def _validate_database_connectivity(self) -> Dict[str, Any]:
        """Validate database connectivity and basic operations"""
        
        checkpoint = {
            'name': 'Database Connectivity',
            'passed': False,
            'errors': [],
            'details': {}
        }
        
        try:
            # Try to make a test request to the database through VRIN API
            test_response = self._make_enterprise_request(
                f"{self.rag_base_url}/health",
                method='GET'
            )
            
            if test_response.status_code == 200:
                health_data = test_response.json()
                
                # Check if database is reported as healthy
                if health_data.get('database_status') == 'healthy':
                    checkpoint['passed'] = True
                    checkpoint['details'] = {
                        'status': 'healthy',
                        'response_time': health_data.get('database_response_time', 'unknown')
                    }
                else:
                    checkpoint['errors'].append(
                        f"❌ Database health check failed:\n"
                        f"   • Status: {health_data.get('database_status', 'unknown')}\n"
                        f"   • Check your Neptune/Cosmos DB configuration\n"
                        f"   • Verify Lambda functions have proper database permissions"
                    )
            else:
                checkpoint['errors'].append(
                    f"❌ Database connectivity test failed:\n"
                    f"   • HTTP {test_response.status_code}: {test_response.text}\n"
                    f"   • Check Lambda function deployment and configuration"
                )
                
        except requests.exceptions.Timeout:
            checkpoint['errors'].append(
                "❌ Database connectivity test timed out:\n"
                "   • Check network connectivity to VRIN API endpoints\n" 
                "   • Verify Lambda functions are deployed and running\n"
                "   • Check VPC and security group configurations"
            )
        except Exception as e:
            checkpoint['errors'].append(
                f"❌ Database connectivity validation failed: {str(e)}\n"
                "   • Verify your infrastructure configuration in VRIN portal\n"
                "   • Check Lambda function logs in CloudWatch"
            )
        
        return checkpoint
    
    def _validate_vector_store_connectivity(self) -> Dict[str, Any]:
        """Validate vector store connectivity"""
        
        checkpoint = {
            'name': 'Vector Store Connectivity', 
            'passed': False,
            'errors': [],
            'details': {}
        }
        
        try:
            # Test vector store through VRIN API
            test_response = self._make_enterprise_request(
                f"{self.rag_base_url}/health",
                method='GET'
            )
            
            if test_response.status_code == 200:
                health_data = test_response.json()
                
                if health_data.get('vector_store_status') == 'healthy':
                    checkpoint['passed'] = True
                    checkpoint['details'] = {
                        'status': 'healthy',
                        'index_name': health_data.get('vector_store_index', 'unknown')
                    }
                else:
                    checkpoint['errors'].append(
                        f"❌ Vector store health check failed:\n"
                        f"   • Status: {health_data.get('vector_store_status', 'unknown')}\n"
                        f"   • Check OpenSearch/Elasticsearch domain configuration\n"
                        f"   • Verify index exists and Lambda has access permissions"
                    )
            else:
                checkpoint['errors'].append(
                    f"❌ Vector store connectivity test failed:\n"
                    f"   • HTTP {test_response.status_code}: {test_response.text}"
                )
                
        except Exception as e:
            checkpoint['errors'].append(
                f"❌ Vector store connectivity validation failed: {str(e)}\n"
                "   • Check OpenSearch/Elasticsearch domain status\n"
                "   • Verify network connectivity and security groups"
            )
        
        return checkpoint
    
    def _validate_llm_connectivity(self) -> Dict[str, Any]:
        """Validate LLM provider connectivity"""
        
        checkpoint = {
            'name': 'LLM Provider Connectivity',
            'passed': False, 
            'errors': [],
            'details': {}
        }
        
        try:
            # Test LLM connectivity through a simple query
            test_response = self._make_enterprise_request(
                f"{self.rag_base_url}/query",
                method='POST',
                data={'query': 'test connectivity', 'test_mode': True}
            )
            
            if test_response.status_code == 200:
                response_data = test_response.json()
                
                if response_data.get('llm_status') == 'healthy':
                    checkpoint['passed'] = True
                    checkpoint['details'] = {
                        'provider': response_data.get('llm_provider', 'unknown'),
                        'model': response_data.get('llm_model', 'unknown')
                    }
                else:
                    checkpoint['errors'].append(
                        f"❌ LLM provider test failed:\n"
                        f"   • Status: {response_data.get('llm_status', 'unknown')}\n"
                        f"   • Check API key configuration in Secrets Manager\n"
                        f"   • Verify Lambda has access to secrets"
                    )
            else:
                checkpoint['errors'].append(
                    f"❌ LLM connectivity test failed:\n"
                    f"   • HTTP {test_response.status_code}: {test_response.text}"
                )
                
        except Exception as e:
            checkpoint['errors'].append(
                f"❌ LLM connectivity validation failed: {str(e)}\n"
                "   • Check OpenAI API key in AWS Secrets Manager\n"
                "   • Verify Lambda execution role has secrets access"
            )
        
        return checkpoint
    
    def _validate_end_to_end_functionality(self) -> Dict[str, Any]:
        """Validate complete end-to-end functionality"""
        
        checkpoint = {
            'name': 'End-to-End Functionality',
            'passed': False,
            'errors': [],
            'details': {}
        }
        
        try:
            # Test basic insert operation
            insert_result = self.insert(
                content="VRIN enterprise test document for validation",
                title="Configuration Test"
            )
            
            if insert_result.get('success'):
                checkpoint['details']['insert_test'] = 'passed'
                
                # Test basic query operation  
                query_result = self.query("test configuration validation")
                
                if query_result.get('success'):
                    checkpoint['passed'] = True
                    checkpoint['details']['query_test'] = 'passed'
                    checkpoint['details']['full_workflow'] = 'operational'
                else:
                    checkpoint['errors'].append(
                        f"❌ Query test failed:\n"
                        f"   • Error: {query_result.get('error', 'Unknown error')}\n"
                        f"   • Check hybrid retrieval configuration"
                    )
            else:
                checkpoint['errors'].append(
                    f"❌ Insert test failed:\n"
                    f"   • Error: {insert_result.get('error', 'Unknown error')}\n"
                    f"   • Check fact extraction and storage configuration"
                )
                
        except Exception as e:
            checkpoint['errors'].append(
                f"❌ End-to-end validation failed: {str(e)}\n"
                "   • Complete system integration may have issues"
            )
        
        return checkpoint
    
    def _check_endpoint_connectivity(self, host: str, port: int, name: str) -> Dict[str, Any]:
        """Check if an endpoint is reachable"""
        
        try:
            # Remove protocol prefix if present
            host = host.replace('https://', '').replace('http://', '').split('/')[0]
            
            socket.setdefaulttimeout(10)
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            
            if port == 443:
                # Use SSL for HTTPS connections
                context = ssl.create_default_context()
                sock = context.wrap_socket(sock, server_hostname=host)
            
            result = sock.connect_ex((host, port))
            sock.close()
            
            if result == 0:
                return {'success': True, 'message': f'{name} is reachable'}
            else:
                return {'success': False, 'error': f'Connection failed (code: {result})'}
                
        except socket.gaierror as e:
            return {'success': False, 'error': f'DNS resolution failed: {str(e)}'}
        except socket.timeout:
            return {'success': False, 'error': 'Connection timed out'}
        except Exception as e:
            return {'success': False, 'error': f'Connection error: {str(e)}'}
    
    def _get_nested_config(self, path: str, default=None):
        """Get nested configuration value using dot notation"""
        
        if not self.configuration:
            return default
        
        keys = path.split('.')
        value = self.configuration
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        
        return value
    
    def _generate_recommendations(self, validation_report: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on validation results"""
        
        recommendations = []
        
        # Configuration recommendations
        if not validation_report['checkpoints'].get('configuration_loading', {}).get('passed'):
            recommendations.append(
                "📋 Complete your infrastructure configuration in VRIN Enterprise Portal:\n"
                "   1. Log into https://enterprise.vrin.ai\n" 
                "   2. Navigate to Infrastructure Configuration\n"
                "   3. Fill in all required database, vector store, and LLM settings\n"
                "   4. Save and validate your configuration"
            )
        
        # Endpoint recommendations
        if not validation_report['checkpoints'].get('endpoint_validation', {}).get('passed'):
            recommendations.append(
                "🌐 Fix network connectivity issues:\n"
                "   1. Check security groups allow Lambda access to your resources\n"
                "   2. Verify VPC routing tables and subnet configuration\n"
                "   3. Ensure NAT Gateway exists for outbound internet access\n"
                "   4. Test connectivity from your VPC to the endpoints"
            )
        
        # Database recommendations
        if not validation_report['checkpoints'].get('database_connectivity', {}).get('passed'):
            recommendations.append(
                "🗄️ Resolve database connectivity:\n"
                "   1. Verify Neptune/Cosmos DB cluster is in 'available' state\n"
                "   2. Check Lambda execution role has database access permissions\n"
                "   3. Ensure database is in the same VPC as Lambda functions\n"
                "   4. Review CloudWatch logs for specific error details"
            )
        
        # Overall recommendation
        if validation_report['overall_status'] != 'passed':
            recommendations.append(
                "🔧 Contact VRIN support if issues persist:\n"
                "   • Email: enterprise-support@vrin.ai\n"
                "   • Include this validation report in your support request\n"
                "   • We can help troubleshoot specific infrastructure issues"
            )
        
        return recommendations
    
    def get_validation_status(self) -> Dict[str, Any]:
        """Get current validation status without running full validation"""
        
        return {
            'validation_results': self.validation_results.copy(),
            'configuration_loaded': bool(self.configuration),
            'organization_context': bool(self.organization_context),
            'last_validation': self.validation_results.get('last_validation'),
            'recommendations': [
                "Run validate_enterprise_configuration() for detailed status"
            ] if not self.validation_results.get('last_validation') else []
        }

# Factory functions for easy client creation
def create_enterprise_client(api_key: str, **kwargs) -> VRINEnterpriseClient:
    """Create an enterprise VRIN client"""
    return VRINEnterpriseClient(api_key, **kwargs)

def create_vpc_isolated_client(api_key: str, vpc_config: Dict[str, Any] = None) -> VRINEnterpriseClient:
    """Create VPC-isolated enterprise client"""
    return VRINEnterpriseClient(
        api_key,
        deployment_mode='vpc_isolated',
        private_endpoints=vpc_config or {}
    )

def create_air_gapped_client(api_key: str, local_endpoints: Dict[str, str]) -> VRINEnterpriseClient:
    """Create air-gapped enterprise client"""
    return VRINEnterpriseClient(
        api_key,
        deployment_mode='air_gapped',
        private_endpoints=local_endpoints
    )

def create_hybrid_explicit_client(api_key: str) -> VRINEnterpriseClient:
    """Create hybrid explicit routing enterprise client"""
    return VRINEnterpriseClient(
        api_key,
        deployment_mode='hybrid_explicit'
    )