"""
VRIN Enterprise Client - Unified Multi-Cloud Enterprise Solution

This consolidated enterprise client combines all deployment models and provider abstractions
into a single, configuration-driven interface for enterprise customers.

Deployment Models:
- Air-gapped: Complete isolation, zero external connectivity  
- VPC-isolated: Private cloud with network isolation
- Hybrid explicit: Client-controlled routing with explicit data handling

Supported Providers:
- AWS: Neptune, OpenSearch, OpenAI
- Azure: Cosmos DB, Cognitive Search, Azure OpenAI
- GCP: Cloud Bigtable, Vertex AI Search, Vertex AI
- On-premise: JanusGraph, Elasticsearch, Local LLM
"""

import logging
from typing import Dict, Any, Optional, List, Union
from datetime import datetime
import json

from .client import VRINClient
from .config import VRINConfig, DeploymentMode
from .providers.factory import ProviderManager
from .validation import validate_and_test_config

logger = logging.getLogger(__name__)


class VRINEnterpriseClient:
    """
    Unified enterprise client that auto-configures based on API key and deployment mode.
    
    Single client interface that replaces client_v2.py and client_v3.py with 
    configuration-driven behavior.
    """
    
    def __init__(self, 
                 api_key: str,
                 config: Optional[Dict[str, Any]] = None,
                 auto_configure: bool = True):
        """
        Initialize enterprise client with automatic configuration detection.
        
        Args:
            api_key: Enterprise API key (vrin_ent_*)
            config: Optional explicit configuration (usually provided by enterprise dashboard)
            auto_configure: Automatically detect deployment mode from API key prefix
        """
        self.api_key = api_key
        self.raw_config = config or {}
        
        # Validate enterprise API key
        if not api_key.startswith('vrin_ent_'):
            raise ValueError(
                "Enterprise client requires enterprise API key (vrin_ent_*). "
                "Use VRINClient for general API keys."
            )
        
        # Auto-detect deployment mode from API key
        self.deployment_mode = self._detect_deployment_mode(api_key)
        
        # Configure based on deployment mode
        if auto_configure:
            self.config = self._auto_configure()
        else:
            self.config = VRINConfig(**self.raw_config) if self.raw_config else None
        
        # Initialize provider manager
        self.provider_manager = ProviderManager(self.config) if self.config else None
        
        # Initialize base client for backward compatibility (if needed)
        self._base_client = None
        
        logger.info(f"Enterprise client initialized in {self.deployment_mode} mode")
    
    def _detect_deployment_mode(self, api_key: str) -> DeploymentMode:
        """Detect deployment mode from API key prefix."""
        if api_key.startswith('vrin_ent_airgap_'):
            return DeploymentMode.AIR_GAPPED
        elif api_key.startswith('vrin_ent_vpc_'):
            return DeploymentMode.VPC_ISOLATED
        elif api_key.startswith('vrin_ent_hybrid_'):
            return DeploymentMode.HYBRID_EXPLICIT
        else:
            # Generic enterprise key - default to hybrid
            return DeploymentMode.HYBRID_EXPLICIT
    
    def _auto_configure(self) -> VRINConfig:
        """
        Auto-configure based on deployment mode and provided configuration.
        
        Configuration priority:
        1. Explicit config parameter
        2. Enterprise dashboard configuration (fetched via API key)
        3. Environment variables
        4. Default configuration for deployment mode
        """
        if self.raw_config:
            # Use explicitly provided config
            return VRINConfig(**self.raw_config)
        
        # Try to fetch configuration from enterprise dashboard
        try:
            dashboard_config = self._fetch_dashboard_config()
            if dashboard_config:
                return VRINConfig(**dashboard_config)
        except Exception as e:
            logger.warning(f"Could not fetch dashboard config: {e}")
        
        # Fall back to default configuration
        return self._get_default_config()
    
    def _fetch_dashboard_config(self) -> Optional[Dict[str, Any]]:
        """
        Fetch configuration from enterprise dashboard API.
        
        This would connect to the enterprise dashboard backend to retrieve
        the organization's infrastructure configuration.
        """
        # TODO: Implement dashboard API integration
        # For now, return None to use default config
        return None
    
    def _get_default_config(self) -> VRINConfig:
        """Get default configuration for the deployment mode."""
        defaults = {
            DeploymentMode.AIR_GAPPED: {
                'deployment_mode': DeploymentMode.AIR_GAPPED,
                'database_provider': 'neptune',  # Will use local Neptune
                'llm_provider': 'openai',        # Will use local OpenAI deployment
                'base_url': None,                # No external API calls
                'require_encryption': True,
                'audit_logging': True
            },
            DeploymentMode.VPC_ISOLATED: {
                'deployment_mode': DeploymentMode.VPC_ISOLATED,
                'database_provider': 'neptune',  # Customer's private Neptune
                'llm_provider': 'openai',        # Customer's private OpenAI
                'base_url': None,                # VPC-internal endpoints only
                'require_encryption': True,
                'private_network_only': True
            },
            DeploymentMode.HYBRID_EXPLICIT: {
                'deployment_mode': DeploymentMode.HYBRID_EXPLICIT,
                'database_provider': 'neptune',
                'llm_provider': 'openai',
                'base_url': 'https://thuiu23t0c.execute-api.us-east-1.amazonaws.com/dev',
                'allow_cloud_processing': True,  # Only with explicit consent
                'require_explicit_routing': True
            }
        }
        
        config_dict = defaults[self.deployment_mode]
        return VRINConfig(**config_dict)
    
    def insert(self, 
               content: str, 
               title: Optional[str] = None,
               metadata: Optional[Dict[str, Any]] = None,
               processing_location: Optional[str] = None) -> Dict[str, Any]:
        """
        Insert content with enterprise security controls.
        
        Args:
            content: Content to insert
            title: Optional title
            metadata: Optional metadata
            processing_location: For hybrid mode - 'private' or 'cloud' (explicit client choice)
        """
        # Validate processing location for hybrid mode
        if self.deployment_mode == DeploymentMode.HYBRID_EXPLICIT:
            if not processing_location:
                processing_location = 'private'  # Default to private for enterprise
            elif processing_location not in ['private', 'cloud']:
                raise ValueError("processing_location must be 'private' or 'cloud' for hybrid mode")
        
        # Route based on deployment mode and processing location
        if (self.deployment_mode in [DeploymentMode.AIR_GAPPED, DeploymentMode.VPC_ISOLATED] or
            (self.deployment_mode == DeploymentMode.HYBRID_EXPLICIT and processing_location == 'private')):
            
            # Process in customer's private infrastructure
            return self._insert_private(content, title, metadata)
        else:
            # Process in VRIN's optimized cloud (only for hybrid mode with explicit consent)
            return self._insert_cloud(content, title, metadata)
    
    def _insert_private(self, content: str, title: Optional[str], metadata: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Insert content using customer's private infrastructure."""
        if not self.provider_manager:
            raise RuntimeError("Provider manager not initialized. Check enterprise configuration.")
        
        # Get database provider (Neptune, Cosmos DB, etc.)
        db_provider = self.provider_manager.get_database_provider()
        llm_provider = self.provider_manager.get_llm_provider()
        
        try:
            # Extract facts using customer's LLM
            facts = llm_provider.extract_facts(content, metadata)
            
            # Store in customer's database
            storage_result = db_provider.store_facts(
                facts, 
                user_id=self._get_user_id(), 
                source_id=self._generate_source_id(content, title)
            )
            
            return {
                'success': True,
                'facts_extracted': len(facts),
                'processing_location': 'private',
                'deployment_mode': self.deployment_mode.value,
                'storage_result': storage_result,
                'processing_time': storage_result.get('processing_time', 'unknown')
            }
            
        except Exception as e:
            logger.error(f"Private insertion failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'processing_location': 'private'
            }
    
    def _insert_cloud(self, content: str, title: Optional[str], metadata: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Insert content using VRIN's optimized cloud infrastructure."""
        # Initialize base client for cloud operations
        if not self._base_client:
            self._base_client = VRINClient(self.api_key)
        
        try:
            # Use standard VRIN cloud processing
            result = self._base_client.insert(content, title, metadata)
            result['processing_location'] = 'cloud'
            result['deployment_mode'] = self.deployment_mode.value
            return result
            
        except Exception as e:
            logger.error(f"Cloud insertion failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'processing_location': 'cloud'
            }
    
    def query(self, 
              query: str,
              processing_location: Optional[str] = None) -> Dict[str, Any]:
        """
        Query knowledge with enterprise security controls.
        
        Args:
            query: Query string
            processing_location: For hybrid mode - 'private' or 'cloud'
        """
        # Apply same routing logic as insert
        if self.deployment_mode == DeploymentMode.HYBRID_EXPLICIT:
            if not processing_location:
                processing_location = 'private'  # Default to private
        
        if (self.deployment_mode in [DeploymentMode.AIR_GAPPED, DeploymentMode.VPC_ISOLATED] or
            (self.deployment_mode == DeploymentMode.HYBRID_EXPLICIT and processing_location == 'private')):
            
            return self._query_private(query)
        else:
            return self._query_cloud(query)
    
    def _query_private(self, query: str) -> Dict[str, Any]:
        """Query using customer's private infrastructure."""
        if not self.provider_manager:
            raise RuntimeError("Provider manager not initialized. Check enterprise configuration.")
        
        try:
            db_provider = self.provider_manager.get_database_provider()
            llm_provider = self.provider_manager.get_llm_provider()
            
            # Search in customer's private database
            facts = db_provider.search_facts(query, user_id=self._get_user_id())
            
            # Generate response using customer's LLM
            response = llm_provider.generate_response(query, facts)
            
            return {
                'success': True,
                'summary': response,
                'total_facts': len(facts),
                'processing_location': 'private',
                'deployment_mode': self.deployment_mode.value
            }
            
        except Exception as e:
            logger.error(f"Private query failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'processing_location': 'private'
            }
    
    def _query_cloud(self, query: str) -> Dict[str, Any]:
        """Query using VRIN's optimized cloud infrastructure."""
        if not self._base_client:
            self._base_client = VRINClient(self.api_key)
        
        try:
            result = self._base_client.query(query)
            result['processing_location'] = 'cloud'
            result['deployment_mode'] = self.deployment_mode.value
            return result
            
        except Exception as e:
            logger.error(f"Cloud query failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'processing_location': 'cloud'
            }
    
    def validate_configuration(self) -> Dict[str, Any]:
        """Validate the current enterprise configuration."""
        if not self.config:
            return {
                'valid': False,
                'error': 'No configuration available'
            }
        
        try:
            return validate_and_test_config(self.config)
        except Exception as e:
            return {
                'valid': False,
                'error': str(e)
            }
    
    def get_deployment_info(self) -> Dict[str, Any]:
        """Get information about the current deployment."""
        return {
            'deployment_mode': self.deployment_mode.value,
            'api_key_prefix': self.api_key[:20] + '...',
            'configuration': {
                'database_provider': self.config.database_provider if self.config else 'unknown',
                'llm_provider': self.config.llm_provider if self.config else 'unknown',
                'private_network_only': getattr(self.config, 'private_network_only', False),
                'require_encryption': getattr(self.config, 'require_encryption', True)
            },
            'capabilities': {
                'air_gapped': self.deployment_mode == DeploymentMode.AIR_GAPPED,
                'vpc_isolated': self.deployment_mode == DeploymentMode.VPC_ISOLATED,
                'hybrid_routing': self.deployment_mode == DeploymentMode.HYBRID_EXPLICIT,
                'cloud_processing': self.deployment_mode == DeploymentMode.HYBRID_EXPLICIT
            }
        }
    
    def _get_user_id(self) -> str:
        """Extract user ID from API key or configuration."""
        # Extract organization ID from enterprise API key
        # vrin_ent_[mode]_[org]_[random] -> extract [org]
        parts = self.api_key.split('_')
        if len(parts) >= 4:
            return parts[3]  # Organization ID
        return 'unknown'
    
    def _generate_source_id(self, content: str, title: Optional[str]) -> str:
        """Generate unique source ID for content."""
        import hashlib
        content_hash = hashlib.md5(content.encode()).hexdigest()[:12]
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        return f"src_{timestamp}_{content_hash}"


# Factory functions for backward compatibility
def create_enterprise_client(api_key: str, **kwargs) -> VRINEnterpriseClient:
    """Create enterprise client with automatic configuration."""
    return VRINEnterpriseClient(api_key, **kwargs)


def create_air_gapped_client(api_key: str, local_config: Dict[str, Any]) -> VRINEnterpriseClient:
    """Create air-gapped enterprise client."""
    if not api_key.startswith('vrin_ent_airgap_'):
        logger.warning("API key should start with 'vrin_ent_airgap_' for air-gapped deployment")
    
    return VRINEnterpriseClient(api_key, config=local_config)


def create_vpc_isolated_client(api_key: str, vpc_config: Dict[str, Any]) -> VRINEnterpriseClient:
    """Create VPC-isolated enterprise client."""
    if not api_key.startswith('vrin_ent_vpc_'):
        logger.warning("API key should start with 'vrin_ent_vpc_' for VPC-isolated deployment")
    
    return VRINEnterpriseClient(api_key, config=vpc_config)


def create_hybrid_client(api_key: str, hybrid_config: Optional[Dict[str, Any]] = None) -> VRINEnterpriseClient:
    """Create hybrid enterprise client with explicit routing."""
    if not api_key.startswith('vrin_ent_hybrid_'):
        logger.warning("API key should start with 'vrin_ent_hybrid_' for hybrid deployment")
    
    return VRINEnterpriseClient(api_key, config=hybrid_config)