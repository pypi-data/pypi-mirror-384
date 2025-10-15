"""
Enhanced VRIN Client with support for multiple deployment configurations.

Supports:
- Centralized deployment (free tier)
- Hybrid cloud deployments (enterprise)
- Multi-provider configurations
- Configuration validation and testing
"""

import requests
import json
import time
import logging
from typing import Dict, List, Any, Optional, Union
from pathlib import Path

from .config import VRINConfig, ConfigManager, DeploymentMode, get_config
from .validation import validate_and_test_config
from .providers.factory import ProviderManager

logger = logging.getLogger(__name__)


class VRINClient:
    """Enhanced VRIN Hybrid RAG Client with multi-deployment support."""
    
    def __init__(self, 
                 api_key: str = None, 
                 config: Optional[VRINConfig] = None,
                 config_path: Optional[str] = None,
                 auto_detect_config: bool = True):
        """
        Initialize VRIN client with flexible configuration.
        
        Args:
            api_key: VRIN API key (for backward compatibility)
            config: VRINConfig instance (for enterprise deployments)
            config_path: Path to configuration file
            auto_detect_config: Automatically detect configuration from environment
        """
        self.api_key = api_key
        self.config = config
        self.config_manager = ConfigManager(config_path)
        
        # Load configuration
        if config:
            self.config = config
        elif config_path or auto_detect_config:
            try:
                self.config = self.config_manager.load_config()
            except Exception as e:
                logger.warning(f"Failed to load config: {str(e)}")
                # Fall back to centralized mode if api_key provided
                if api_key:
                    self.config = ConfigManager.create_centralized_config(api_key)
                else:
                    raise ValueError("Must provide either api_key or valid configuration")
        else:
            if not api_key:
                raise ValueError("Must provide api_key when not using configuration file")
            self.config = ConfigManager.create_centralized_config(api_key)
            
        # Extract API key from config if not provided
        if not self.api_key and self.config.llm.api_key:
            self.api_key = self.config.llm.api_key
            
        # Determine endpoints based on deployment mode
        self._setup_endpoints()
        
        # Initialize provider manager for direct database access (optional)
        self._provider_manager: Optional[ProviderManager] = None
        
    def _setup_endpoints(self):
        """Setup API endpoints based on configuration."""
        if self.config.deployment_mode == DeploymentMode.CENTRALIZED:
            # Use VRIN's centralized APIs
            self.rag_base_url = "https://thuiu23t0c.execute-api.us-east-1.amazonaws.com/dev"
            self.auth_base_url = "https://gp7g651udc.execute-api.us-east-1.amazonaws.com/Prod"
        else:
            # For hybrid/distributed, check if custom endpoints are configured
            self.rag_base_url = getattr(self.config, 'rag_api_endpoint', 
                                      "https://thuiu23t0c.execute-api.us-east-1.amazonaws.com/dev")
            self.auth_base_url = getattr(self.config, 'auth_api_endpoint',
                                       "https://gp7g651udc.execute-api.us-east-1.amazonaws.com/Prod")
                                       
        # Headers for API requests
        self.headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.api_key}',
            'X-VRIN-Deployment-Mode': self.config.deployment_mode.value,
            'X-VRIN-Config-Version': '2.0'
        }

        if self.config.organization_id:
            self.headers['X-VRIN-Organization-ID'] = self.config.organization_id

        # Conversation state tracking
        self._current_session_id: Optional[str] = None
        self._conversation_history: List[str] = []  # Track session IDs
            
    def get_deployment_info(self) -> Dict[str, Any]:
        """Get deployment information and configuration."""
        return {
            'deployment_mode': self.config.deployment_mode.value,
            'database_provider': self.config.database.provider.value,
            'llm_provider': self.config.llm.provider.value,
            'organization_id': self.config.organization_id,
            'endpoints': {
                'rag_api': self.rag_base_url,
                'auth_api': self.auth_base_url
            },
            'configuration_valid': self._validate_config_quick()
        }
        
    def validate_configuration(self, test_connectivity: bool = True) -> Dict[str, Any]:
        """Validate current configuration and optionally test connectivity."""
        if test_connectivity:
            return validate_and_test_config(self.config)
        else:
            from .validation import ConfigValidator
            validator = ConfigValidator()
            is_valid, issues = validator.validate_config(self.config)
            
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
                'overall_status': 'valid' if is_valid else 'invalid'
            }
            
    def health_check(self) -> Dict[str, Any]:
        """Check health of VRIN services and configuration."""
        try:
            # Check API health
            api_health = self._check_api_health()
            
            # Check provider health (if using direct provider access)
            provider_health = {}
            if self._provider_manager:
                provider_health = self._provider_manager.health_check()
                
            overall_status = 'healthy' if (
                api_health.get('status') == 'healthy' and
                (not provider_health or provider_health.get('overall', {}).get('status') == 'healthy')
            ) else 'unhealthy'
            
            return {
                'overall_status': overall_status,
                'api_health': api_health,
                'provider_health': provider_health,
                'configuration': self.get_deployment_info(),
                'timestamp': int(time.time())
            }
            
        except Exception as e:
            logger.error(f"Health check failed: {str(e)}")
            return {
                'overall_status': 'error',
                'error': str(e),
                'timestamp': int(time.time())
            }
            
    def _check_api_health(self) -> Dict[str, Any]:
        """Check API endpoint health."""
        try:
            response = requests.get(
                f"{self.rag_base_url}/health",
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            
            if response.status_code == 200:
                return {'status': 'healthy', 'response_time': response.elapsed.total_seconds()}
            else:
                return {'status': 'unhealthy', 'status_code': response.status_code}
                
        except requests.exceptions.RequestException as e:
            return {'status': 'error', 'error': str(e)}
            
    def insert(self,
               content: str,
               title: str = "Untitled",
               metadata: Optional[Dict[str, Any]] = None,
               tags: Optional[List[str]] = None,
               wait: bool = True,
               poll_interval: int = 2,
               max_wait: int = 300) -> Union[Dict[str, Any], str]:
        """
        Insert content into knowledge base with async processing (v0.8.0+).

        The backend now processes insertions asynchronously by default to avoid
        API Gateway timeout issues. This method handles the async workflow transparently.

        Args:
            content: Text content to insert
            title: Content title
            metadata: Additional metadata
            tags: Content tags
            wait: If True (default), poll until completion and return results.
                  If False, return job_id immediately for manual status checking.
            poll_interval: Seconds between status checks when wait=True (default: 2s)
            max_wait: Maximum seconds to wait when wait=True (default: 300s)

        Returns:
            If wait=True: Dict containing extraction results (backward compatible)
            If wait=False: String job_id for manual polling via get_job_status()

        Example:
            # Default: Wait for completion (backward compatible)
            result = client.insert("content...", title="Doc")
            print(f"Extracted {result['facts_extracted']} facts")

            # Advanced: Get job_id immediately
            job_id = client.insert("content...", wait=False)
            status = client.get_job_status(job_id)
        """
        try:
            payload = {
                'content': content,
                'title': title,
                'metadata': metadata or {},
                'tags': tags or []
            }

            # Add configuration context for enterprise deployments
            if self.config.deployment_mode != DeploymentMode.CENTRALIZED:
                payload['deployment_context'] = {
                    'mode': self.config.deployment_mode.value,
                    'organization_id': self.config.organization_id
                }

            # POST to /insert - backend returns job_id immediately (v0.8.0+)
            response = requests.post(
                f"{self.rag_base_url}/insert",
                headers=self.headers,
                json=payload,
                timeout=30  # Short timeout since backend returns immediately
            )

            response.raise_for_status()
            result = response.json()

            # Backend returns: {'success': True, 'job_id': '...', 'status': 'pending', ...}
            job_id = result.get('job_id')

            if not job_id:
                # Fallback for older backend versions (synchronous response)
                logger.warning("Backend did not return job_id, assuming synchronous processing")
                result['client_info'] = {
                    'deployment_mode': self.config.deployment_mode.value,
                    'database_provider': self.config.database.provider.value,
                    'llm_provider': self.config.llm.provider.value,
                    'api_version': '2.0'
                }
                return result

            # If wait=False, return job_id immediately
            if not wait:
                return job_id

            # If wait=True, poll until completion
            logger.info(f"Job {job_id} created, polling for completion (max {max_wait}s)...")
            final_result = self.wait_for_job(job_id, poll_interval, max_wait)

            # Add client-side metadata to final result
            final_result['client_info'] = {
                'deployment_mode': self.config.deployment_mode.value,
                'database_provider': self.config.database.provider.value,
                'llm_provider': self.config.llm.provider.value,
                'api_version': '2.0',
                'job_id': job_id
            }

            return final_result

        except requests.exceptions.RequestException as e:
            logger.error(f"Insert request failed: {str(e)}")
            return {
                'success': False,
                'error': f'Request failed: {str(e)}',
                'status_code': getattr(e.response, 'status_code', None)
            }
        except Exception as e:
            logger.error(f"Insert operation failed: {str(e)}")
            return {
                'success': False,
                'error': f'Operation failed: {str(e)}'
            }

    def get_job_status(self, job_id: str) -> Dict[str, Any]:
        """
        Get current status of an async insertion job.

        Args:
            job_id: Job ID returned from insert(wait=False)

        Returns:
            Dict containing job status information:
            {
                'job_id': str,
                'status': str,  # 'pending', 'chunking', 'extracting', 'storing', 'completed', 'failed'
                'timestamp': int,
                'data': dict,  # Contains results when status='completed'
                'progress': float,  # 0.0 to 1.0
                'message': str,
                'error_details': str  # Only present if status='failed'
            }

        Example:
            job_id = client.insert("content...", wait=False)
            status = client.get_job_status(job_id)
            print(f"Job {job_id}: {status['status']} ({status['progress']*100}%)")
        """
        try:
            response = requests.get(
                f"{self.rag_base_url}/job-status/{job_id}",
                headers=self.headers,
                timeout=10
            )

            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as e:
            logger.error(f"Job status request failed: {str(e)}")
            return {
                'success': False,
                'error': f'Request failed: {str(e)}',
                'status_code': getattr(e.response, 'status_code', None)
            }
        except Exception as e:
            logger.error(f"Job status operation failed: {str(e)}")
            return {
                'success': False,
                'error': f'Operation failed: {str(e)}'
            }

    def wait_for_job(self, job_id: str, poll_interval: int = 2, max_wait: int = 300) -> Dict[str, Any]:
        """
        Poll job status until completion or timeout.

        Args:
            job_id: Job ID to wait for
            poll_interval: Seconds between status checks (default: 2s)
            max_wait: Maximum seconds to wait (default: 300s)

        Returns:
            Dict containing final job results (status['data'])

        Raises:
            TimeoutError: If job doesn't complete within max_wait seconds
            Exception: If job fails with error

        Example:
            job_id = client.insert("content...", wait=False)
            # Do other work...
            result = client.wait_for_job(job_id)
            print(f"Extracted {result['facts_extracted']} facts")
        """
        start_time = time.time()
        last_status = None

        while (time.time() - start_time) < max_wait:
            status = self.get_job_status(job_id)

            # Handle API errors
            if not status.get('success', True) or 'error' in status:
                logger.error(f"Error checking job status: {status.get('error')}")
                time.sleep(poll_interval)
                continue

            current_status = status.get('status')

            # Log progress if status changed
            if current_status != last_status:
                progress = status.get('progress', 0) * 100
                message = status.get('message', '')
                logger.info(f"Job {job_id}: {current_status} ({progress:.1f}%) - {message}")
                last_status = current_status

            # Check if completed
            if current_status == 'completed':
                logger.info(f"Job {job_id} completed successfully")
                return status.get('data', {})

            # Check if failed
            if current_status == 'failed':
                error_details = status.get('error_details', 'Unknown error')
                logger.error(f"Job {job_id} failed: {error_details}")
                raise Exception(f"Job failed: {error_details}")

            # Wait before next poll
            time.sleep(poll_interval)

        # Timeout
        elapsed = time.time() - start_time
        logger.error(f"Job {job_id} did not complete within {max_wait}s (status: {last_status})")
        raise TimeoutError(
            f"Job {job_id} did not complete within {max_wait}s. "
            f"Last status: {last_status}. Use get_job_status() to check current state."
        )

    def insert_and_wait(self, content: str, title: str = "Untitled", tags: List[str] = None, timeout: int = 300) -> Dict[str, Any]:
        """
        Insert content and wait for processing to complete.

        DEPRECATED: Use insert() with wait=True (default) instead.
        Kept for backward compatibility.

        Args:
            content: Text content to insert
            title: Content title
            tags: Optional list of tags
            timeout: Maximum time to wait in seconds

        Returns:
            Dict containing processing results
        """
        return self.insert(content, title=title, tags=tags, wait=True, max_wait=timeout)

    def query(self,
              query_text: str,
              max_results: int = 10,
              include_reasoning: bool = True,
              specialization_context: Optional[Dict[str, Any]] = None,
              maintain_context: bool = False,
              session_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Query knowledge base with enhanced reasoning and specialization.

        Args:
            query_text: Query text
            max_results: Maximum results to return
            include_reasoning: Include multi-hop reasoning
            specialization_context: User specialization context
            maintain_context: If True, maintains conversation context across queries
            session_id: Optional session ID to continue existing conversation

        Returns:
            Dict containing query results with reasoning chains and optional session info
        """
        try:
            payload = {
                'query': query_text,
                'max_results': max_results,
                'include_reasoning': include_reasoning,
                'deployment_mode': self.config.deployment_mode.value,
                'maintain_context': maintain_context
            }

            if specialization_context:
                payload['specialization_context'] = specialization_context

            if session_id:
                payload['session_id'] = session_id

            response = requests.post(
                f"{self.rag_base_url}/query",
                headers=self.headers,
                json=payload,
                timeout=90  # Longer timeout for complex reasoning and table queries
            )

            response.raise_for_status()
            result = response.json()

            # Store session_id for potential follow-up queries
            if maintain_context and result.get('session_id'):
                self._current_session_id = result['session_id']

            # Add client-side metadata
            result['client_info'] = {
                'deployment_mode': self.config.deployment_mode.value,
                'query_timestamp': int(time.time()),
                'api_version': '2.0'
            }

            return result
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Query request failed: {str(e)}")
            return {
                'success': False,
                'error': f'Request failed: {str(e)}',
                'status_code': getattr(e.response, 'status_code', None)
            }
        except Exception as e:
            logger.error(f"Query operation failed: {str(e)}")
            return {
                'success': False,
                'error': f'Operation failed: {str(e)}'
            }
            
    def specialize(self,
                   custom_prompt: str,
                   reasoning_focus: Optional[List[str]] = None,
                   analysis_depth: str = "detailed",
                   domain_keywords: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Configure user-defined AI specialization.
        
        Args:
            custom_prompt: Custom expert persona prompt
            reasoning_focus: List of reasoning focuses
            analysis_depth: Analysis depth (surface, detailed, expert)
            domain_keywords: Domain-specific keywords
            
        Returns:
            Dict containing specialization configuration result
        """
        try:
            payload = {
                'specialization': {
                    'custom_prompt': custom_prompt,
                    'reasoning_focus': reasoning_focus or [],
                    'analysis_depth': analysis_depth,
                    'domain_keywords': domain_keywords or []
                },
                'deployment_mode': self.config.deployment_mode.value
            }
            
            response = requests.post(
                f"{self.rag_base_url}/specialize",
                headers=self.headers,
                json=payload,
                timeout=30
            )
            
            response.raise_for_status()
            result = response.json()
            
            return result
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Specialization request failed: {str(e)}")
            return {
                'success': False,
                'error': f'Request failed: {str(e)}',
                'status_code': getattr(e.response, 'status_code', None)
            }
        except Exception as e:
            logger.error(f"Specialization operation failed: {str(e)}")
            return {
                'success': False,
                'error': f'Operation failed: {str(e)}'
            }
            
    def get_knowledge_graph(self, 
                           user_id: Optional[str] = None,
                           limit: int = 100,
                           format: str = "json") -> Dict[str, Any]:
        """
        Get knowledge graph visualization data.
        
        Args:
            user_id: Specific user ID (for enterprise deployments)
            limit: Maximum nodes/edges to return
            format: Output format (json, cytoscape, d3)
            
        Returns:
            Dict containing graph data
        """
        try:
            params = {
                'limit': limit,
                'format': format
            }
            
            if user_id:
                params['user_id'] = user_id
                
            response = requests.get(
                f"{self.rag_base_url}/graph",
                headers=self.headers,
                params=params,
                timeout=30
            )
            
            response.raise_for_status()
            result = response.json()
            
            return result
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Graph request failed: {str(e)}")
            return {
                'success': False,
                'error': f'Request failed: {str(e)}',
                'status_code': getattr(e.response, 'status_code', None)
            }
        except Exception as e:
            logger.error(f"Graph operation failed: {str(e)}")
            return {
                'success': False,
                'error': f'Operation failed: {str(e)}'
            }
            
    def direct_database_access(self) -> Optional[ProviderManager]:
        """
        Get direct database provider access for advanced operations.
        Only available for hybrid/distributed deployments.
        
        Returns:
            ProviderManager instance or None
        """
        if self.config.deployment_mode == DeploymentMode.CENTRALIZED:
            logger.warning("Direct database access not available in centralized mode")
            return None
            
        if not self._provider_manager:
            try:
                self._provider_manager = ProviderManager(self.config)
                if not self._provider_manager.connect():
                    logger.error("Failed to connect to providers")
                    return None
            except Exception as e:
                logger.error(f"Failed to initialize provider manager: {str(e)}")
                return None
                
        return self._provider_manager
        
    def save_configuration(self, config_path: Optional[str] = None) -> bool:
        """Save current configuration to file."""
        return self.config_manager.save_config(self.config, config_path)
        
    def _validate_config_quick(self) -> bool:
        """Quick configuration validation."""
        try:
            required_fields = [
                self.config.deployment_mode,
                self.config.database.provider,
                self.config.database.endpoint,
                self.config.llm.provider,
                self.config.llm.api_key
            ]
            return all(field is not None for field in required_fields)
        except Exception:
            return False
            
    def __enter__(self):
        """Context manager entry."""
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - cleanup provider connections."""
        if self._provider_manager:
            self._provider_manager.disconnect()
            
    # Backward compatibility methods
    def insert_text(self, text: str, title: str = None, tags: List[str] = None) -> Dict[str, Any]:
        """Backward compatibility method for insert_text."""
        return self.insert(text, title or "Untitled", tags=tags)
        
    # Conversation State Management Methods

    def start_conversation(self, user_specialization_id: Optional[str] = None) -> 'VRINClient':
        """
        Start a new conversation session.

        Args:
            user_specialization_id: Optional custom AI expert configuration

        Returns:
            self (for method chaining)

        Example:
            client.start_conversation()
            response1 = client.query("What was Cadence's 2010 stock value?", maintain_context=True)
            response2 = client.query("What about 2011?", maintain_context=True)
        """
        self._current_session_id = None
        self._pending_specialization_id = user_specialization_id
        logger.info("Started new conversation session")
        return self

    def continue_conversation(self, query_text: str, **kwargs) -> Dict[str, Any]:
        """
        Query with automatic conversation context maintenance.

        Args:
            query_text: The question to ask
            **kwargs: Additional parameters to pass to query()

        Returns:
            Query result with session information

        Example:
            client.start_conversation()
            response1 = client.continue_conversation("What was Cadence's 2010 stock value?")
            response2 = client.continue_conversation("What about 2011?")  # Uses context from response1
        """
        # Force maintain_context=True and use current session if available
        kwargs['maintain_context'] = True
        if self._current_session_id:
            kwargs['session_id'] = self._current_session_id

        return self.query(query_text, **kwargs)

    def end_conversation(self) -> 'VRINClient':
        """
        End current conversation session.

        Returns:
            self (for method chaining)
        """
        if self._current_session_id:
            self._conversation_history.append(self._current_session_id)
            logger.info(f"Ended conversation session: {self._current_session_id}")
            self._current_session_id = None
        return self

    def get_current_session_id(self) -> Optional[str]:
        """
        Get the current conversation session ID.

        Returns:
            Current session ID or None if no active conversation
        """
        return self._current_session_id

    def get_conversation_history_ids(self) -> List[str]:
        """
        Get list of previous conversation session IDs.

        Returns:
            List of session IDs from ended conversations
        """
        return self._conversation_history.copy()

    # Backward compatibility

    def query_text(self, query: str) -> Dict[str, Any]:
        """Backward compatibility method for query_text."""
        return self.query(query)
        

# Factory functions for different deployment types
def create_centralized_client(api_key: str) -> VRINClient:
    """Create client for centralized (free tier) deployment."""
    config = ConfigManager.create_centralized_config(api_key)
    return VRINClient(config=config)


def create_hybrid_aws_client(
    neptune_endpoint: str,
    openai_api_key: str,
    vpc_id: str,
    subnet_ids: List[str],
    organization_id: str = None
) -> VRINClient:
    """Create client for hybrid AWS deployment."""
    config = ConfigManager.create_hybrid_aws_config(
        neptune_endpoint, openai_api_key, vpc_id, subnet_ids, 
        organization_id=organization_id
    )
    return VRINClient(config=config)


def create_hybrid_azure_client(
    cosmos_account: str,
    cosmos_key: str,
    azure_openai_endpoint: str,
    azure_openai_key: str,
    deployment_name: str,
    organization_id: str = None
) -> VRINClient:
    """Create client for hybrid Azure deployment.""" 
    config = ConfigManager.create_hybrid_azure_config(
        cosmos_account, cosmos_key, azure_openai_endpoint,
        azure_openai_key, deployment_name, organization_id=organization_id
    )
    return VRINClient(config=config)


def create_client_from_config(config_path: str) -> VRINClient:
    """Create client from configuration file."""
    return VRINClient(config_path=config_path)


def create_vpc_isolated_client(
    neptune_endpoint: str,
    openai_api_key: str,
    vpc_id: str,
    subnet_ids: List[str],
    security_group_ids: List[str],
    connectivity_type: str = "PrivateLink",
    region: str = "us-east-1",
    organization_id: str = None
) -> VRINClient:
    """Create client for VPC-isolated enterprise deployment."""
    from .config import create_vpc_isolated_config
    
    config = create_vpc_isolated_config(
        neptune_endpoint=neptune_endpoint,
        openai_api_key=openai_api_key,
        vpc_id=vpc_id,
        subnet_ids=subnet_ids,
        security_group_ids=security_group_ids,
        connectivity_type=connectivity_type,
        region=region,
        organization_id=organization_id
    )
    
    return VRINClient(config=config)