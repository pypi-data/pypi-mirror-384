"""
Provider factory for VRIN hybrid cloud architecture.

Instantiates appropriate database and LLM providers based on configuration.
"""

import logging
from typing import Dict, Any, Optional, Tuple

from ..config import VRINConfig, DatabaseProvider as DBProvider, LLMProvider as LLMProv
from .database import (
    GraphDatabaseProvider, 
    NeptuneProvider, 
    CosmosDBProvider, 
    JanusGraphProvider
)
from .llm import (
    LLMProvider,
    OpenAIProvider, 
    AzureOpenAIProvider
)

logger = logging.getLogger(__name__)


class ProviderFactory:
    """Factory for creating database and LLM providers."""
    
    @staticmethod
    def create_database_provider(config: VRINConfig) -> Optional[GraphDatabaseProvider]:
        """Create database provider based on configuration."""
        db_config = config.database
        
        try:
            # Prepare provider configuration
            provider_config = {
                'endpoint': db_config.endpoint,
                'port': db_config.port,
                'region': db_config.region,
            }
            
            # Add credentials if available
            if db_config.credentials:
                provider_config.update(db_config.credentials)
                
            # Add additional parameters
            if db_config.additional_params:
                provider_config.update(db_config.additional_params)
                
            # Create provider based on type
            if db_config.provider == DBProvider.NEPTUNE:
                return NeptuneProvider(provider_config)
                
            elif db_config.provider == DBProvider.COSMOS_DB:
                return CosmosDBProvider(provider_config)
                
            elif db_config.provider == DBProvider.JANUSGRAPH:
                return JanusGraphProvider(provider_config)
                
            else:
                logger.error(f"Unsupported database provider: {db_config.provider}")
                return None
                
        except Exception as e:
            logger.error(f"Failed to create database provider: {str(e)}")
            return None
            
    @staticmethod
    def create_llm_provider(config: VRINConfig) -> Optional[LLMProvider]:
        """Create LLM provider based on configuration.""" 
        llm_config = config.llm
        
        try:
            # Prepare provider configuration
            provider_config = {
                'api_key': llm_config.api_key,
                'model': llm_config.model,
                'temperature': llm_config.temperature,
                'max_tokens': llm_config.max_tokens,
                'endpoint': llm_config.endpoint,
            }
            
            # Add additional parameters
            if llm_config.additional_params:
                provider_config.update(llm_config.additional_params)
                
            # Create provider based on type
            if llm_config.provider == LLMProv.OPENAI:
                return OpenAIProvider(provider_config)
                
            elif llm_config.provider == LLMProv.AZURE_OPENAI:
                # Extract Azure-specific config
                if llm_config.endpoint and 'openai.azure.com' in llm_config.endpoint:
                    # Parse resource name from endpoint
                    resource_name = llm_config.endpoint.split('//')[1].split('.')[0]
                    provider_config['resource_name'] = resource_name
                    
                if llm_config.additional_params:
                    provider_config['deployment_name'] = llm_config.additional_params.get('deployment_name', llm_config.model)
                    provider_config['api_version'] = llm_config.additional_params.get('api_version', '2023-12-01-preview')
                    
                return AzureOpenAIProvider(provider_config)
                
            else:
                logger.error(f"Unsupported LLM provider: {llm_config.provider}")
                return None
                
        except Exception as e:
            logger.error(f"Failed to create LLM provider: {str(e)}")
            return None
            
    @staticmethod
    def create_providers(config: VRINConfig) -> Tuple[Optional[GraphDatabaseProvider], Optional[LLMProvider]]:
        """Create both database and LLM providers."""
        db_provider = ProviderFactory.create_database_provider(config)
        llm_provider = ProviderFactory.create_llm_provider(config)
        
        return db_provider, llm_provider
        
    @staticmethod
    def test_providers(config: VRINConfig) -> Dict[str, Any]:
        """Test provider connectivity and return health status."""
        results = {
            'database': {'status': 'not_tested'},
            'llm': {'status': 'not_tested'},
            'overall': {'status': 'unknown'}
        }
        
        try:
            # Test database provider
            db_provider = ProviderFactory.create_database_provider(config)
            if db_provider:
                if db_provider.connect():
                    results['database'] = db_provider.health_check()
                    db_provider.disconnect()
                else:
                    results['database'] = {'status': 'connection_failed'}
            else:
                results['database'] = {'status': 'provider_creation_failed'}
                
        except Exception as e:
            results['database'] = {'status': 'error', 'error': str(e)}
            
        try:
            # Test LLM provider
            llm_provider = ProviderFactory.create_llm_provider(config)
            if llm_provider:
                results['llm'] = llm_provider.health_check()
            else:
                results['llm'] = {'status': 'provider_creation_failed'}
                
        except Exception as e:
            results['llm'] = {'status': 'error', 'error': str(e)}
            
        # Determine overall status
        db_healthy = results['database'].get('status') == 'healthy'
        llm_healthy = results['llm'].get('status') == 'healthy'
        
        if db_healthy and llm_healthy:
            results['overall'] = {'status': 'healthy', 'message': 'All providers operational'}
        elif db_healthy or llm_healthy:
            results['overall'] = {'status': 'degraded', 'message': 'Some providers operational'}
        else:
            results['overall'] = {'status': 'unhealthy', 'message': 'No providers operational'}
            
        return results


class ProviderManager:
    """Manages provider instances with connection pooling."""
    
    def __init__(self, config: VRINConfig):
        """Initialize provider manager with configuration."""
        self.config = config
        self._db_provider: Optional[GraphDatabaseProvider] = None
        self._llm_provider: Optional[LLMProvider] = None
        self._connected = False
        
    def connect(self) -> bool:
        """Connect to providers."""
        try:
            # Create providers
            self._db_provider, self._llm_provider = ProviderFactory.create_providers(self.config)
            
            if not self._db_provider or not self._llm_provider:
                logger.error("Failed to create providers")
                return False
                
            # Connect to database
            if not self._db_provider.connect():
                logger.error("Failed to connect to database provider")
                return False
                
            self._connected = True
            logger.info(f"Connected to providers: {self.config.database.provider.value}, {self.config.llm.provider.value}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect providers: {str(e)}")
            return False
            
    def disconnect(self) -> None:
        """Disconnect from providers."""
        try:
            if self._db_provider:
                self._db_provider.disconnect()
                
            self._db_provider = None
            self._llm_provider = None
            self._connected = False
            
            logger.info("Disconnected from providers")
            
        except Exception as e:
            logger.error(f"Error disconnecting providers: {str(e)}")
            
    def get_database_provider(self) -> Optional[GraphDatabaseProvider]:
        """Get database provider instance."""
        if not self._connected:
            logger.warning("Providers not connected")
            return None
            
        return self._db_provider
        
    def get_llm_provider(self) -> Optional[LLMProvider]:
        """Get LLM provider instance."""
        if not self._connected:
            logger.warning("Providers not connected")
            return None
            
        return self._llm_provider
        
    def health_check(self) -> Dict[str, Any]:
        """Check health of all providers."""
        if not self._connected:
            return {
                'database': {'status': 'not_connected'},
                'llm': {'status': 'not_connected'},
                'overall': {'status': 'not_connected'}
            }
            
        results = {}
        
        # Check database health
        if self._db_provider:
            results['database'] = self._db_provider.health_check()
        else:
            results['database'] = {'status': 'not_available'}
            
        # Check LLM health
        if self._llm_provider:
            results['llm'] = self._llm_provider.health_check()
        else:
            results['llm'] = {'status': 'not_available'}
            
        # Overall status
        db_healthy = results['database'].get('status') == 'healthy'
        llm_healthy = results['llm'].get('status') == 'healthy'
        
        if db_healthy and llm_healthy:
            results['overall'] = {'status': 'healthy'}
        elif db_healthy or llm_healthy:
            results['overall'] = {'status': 'degraded'}
        else:
            results['overall'] = {'status': 'unhealthy'}
            
        return results
        
    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.disconnect()


# Global provider manager instance  
_provider_manager: Optional[ProviderManager] = None

def get_provider_manager(config: Optional[VRINConfig] = None) -> ProviderManager:
    """Get global provider manager instance."""
    global _provider_manager
    
    if _provider_manager is None or (config and config != _provider_manager.config):
        if config is None:
            from ..config import get_config
            config = get_config()
            
        _provider_manager = ProviderManager(config)
        
    return _provider_manager


def get_database_provider(config: Optional[VRINConfig] = None) -> Optional[GraphDatabaseProvider]:
    """Get database provider instance.""" 
    manager = get_provider_manager(config)
    if not manager._connected:
        manager.connect()
    return manager.get_database_provider()


def get_llm_provider(config: Optional[VRINConfig] = None) -> Optional[LLMProvider]:
    """Get LLM provider instance."""
    manager = get_provider_manager(config)
    if not manager._connected:
        manager.connect()
    return manager.get_llm_provider()