"""
Configuration management for VRIN enterprise hybrid cloud architecture.

Supports multiple deployment modes:
- Centralized (free tier): All services on VRIN AWS
- Hybrid (enterprise): Customer database + VRIN compute
- Fully distributed (enterprise): Customer controls all components
"""

import json
import os
import logging
from enum import Enum
from typing import Dict, Any, Optional, Union, List
from dataclasses import dataclass, asdict
from pathlib import Path

logger = logging.getLogger(__name__)


class DeploymentMode(Enum):
    """Deployment modes for VRIN."""
    CENTRALIZED = "centralized"      # Free tier - all on VRIN AWS
    HYBRID = "hybrid"               # Enterprise - customer DB, VRIN compute
    DISTRIBUTED = "distributed"    # Enterprise - customer controls all
    AIR_GAPPED = "air_gapped"       # Enterprise - completely isolated
    VPC_ISOLATED = "vpc_isolated"   # Enterprise - VPC network isolation  
    HYBRID_EXPLICIT = "hybrid_explicit"  # Enterprise - client-controlled routing


class DatabaseProvider(Enum):
    """Supported database providers."""
    NEPTUNE = "neptune"             # AWS Neptune
    COSMOS_DB = "cosmos_db"         # Azure Cosmos DB
    JANUSGRAPH = "janusgraph"       # Open source JanusGraph
    NEO4J = "neo4j"                # Neo4j (future)


class LLMProvider(Enum):
    """Supported LLM providers.""" 
    OPENAI = "openai"               # OpenAI API
    AZURE_OPENAI = "azure_openai"   # Azure OpenAI Service
    CUSTOMER = "customer"           # Customer-hosted model


@dataclass
class DatabaseConfig:
    """Database configuration."""
    provider: DatabaseProvider
    endpoint: Optional[str] = None
    port: Optional[int] = None
    region: Optional[str] = None
    credentials: Optional[Dict[str, str]] = None
    additional_params: Optional[Dict[str, Any]] = None
    
    
@dataclass 
class LLMConfig:
    """LLM configuration."""
    provider: LLMProvider
    model: str = "gpt-4o-mini"
    api_key: Optional[str] = None
    endpoint: Optional[str] = None
    temperature: float = 0.1
    max_tokens: int = 2000
    additional_params: Optional[Dict[str, Any]] = None


@dataclass
class NetworkConfig:
    """Network and connectivity configuration."""
    vpc_id: Optional[str] = None
    subnet_ids: Optional[list] = None
    security_group_ids: Optional[list] = None
    private_link_endpoint: Optional[str] = None
    vpn_connection: Optional[Dict[str, str]] = None
    direct_connect: Optional[Dict[str, str]] = None
    

@dataclass
class SecurityConfig:
    """Security and compliance configuration."""
    encryption_at_rest: bool = True
    encryption_in_transit: bool = True
    customer_managed_keys: Optional[Dict[str, str]] = None
    audit_logging: bool = True
    data_residency_region: Optional[str] = None
    compliance_standards: Optional[list] = None
    

@dataclass
class VRINConfig:
    """Complete VRIN configuration."""
    deployment_mode: DeploymentMode
    database: DatabaseConfig
    llm: LLMConfig
    network: Optional[NetworkConfig] = None
    security: Optional[SecurityConfig] = None
    user_id: Optional[str] = None
    organization_id: Optional[str] = None
    additional_config: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'VRINConfig':
        """Create from dictionary."""
        return cls(
            deployment_mode=DeploymentMode(data['deployment_mode']),
            database=DatabaseConfig(
                provider=DatabaseProvider(data['database']['provider']),
                **{k: v for k, v in data['database'].items() if k != 'provider'}
            ),
            llm=LLMConfig(
                provider=LLMProvider(data['llm']['provider']),
                **{k: v for k, v in data['llm'].items() if k != 'provider'}
            ),
            network=NetworkConfig(**data['network']) if data.get('network') else None,
            security=SecurityConfig(**data['security']) if data.get('security') else None,
            user_id=data.get('user_id'),
            organization_id=data.get('organization_id'),
            additional_config=data.get('additional_config')
        )


class ConfigManager:
    """Configuration manager for VRIN deployments."""
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize config manager."""
        self.config_path = config_path or os.getenv('VRIN_CONFIG_PATH', 'vrin_config.json')
        self._config: Optional[VRINConfig] = None
        
    def load_config(self, config_path: Optional[str] = None) -> VRINConfig:
        """Load configuration from file or environment."""
        if config_path:
            self.config_path = config_path
            
        # Try loading from file first
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r') as f:
                    config_data = json.load(f)
                self._config = VRINConfig.from_dict(config_data)
                logger.info(f"Loaded config from {self.config_path}")
                return self._config
            except Exception as e:
                logger.error(f"Failed to load config from file: {str(e)}")
                
        # Fall back to environment variables
        self._config = self._load_from_environment()
        logger.info("Loaded config from environment variables")
        return self._config
        
    def save_config(self, config: VRINConfig, config_path: Optional[str] = None) -> bool:
        """Save configuration to file."""
        save_path = config_path or self.config_path
        
        try:
            # Ensure directory exists
            Path(save_path).parent.mkdir(parents=True, exist_ok=True)
            
            with open(save_path, 'w') as f:
                json.dump(config.to_dict(), f, indent=2, default=str)
                
            self._config = config
            logger.info(f"Saved config to {save_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save config: {str(e)}")
            return False
            
    def get_config(self) -> VRINConfig:
        """Get current configuration."""
        if self._config is None:
            self._config = self.load_config()
        return self._config
        
    def update_config(self, **kwargs) -> VRINConfig:
        """Update configuration with new values."""
        current = self.get_config()
        
        # Update fields that are provided
        for key, value in kwargs.items():
            if hasattr(current, key):
                setattr(current, key, value)
                
        self._config = current
        return current
        
    def _load_from_environment(self) -> VRINConfig:
        """Load configuration from environment variables."""
        # Determine deployment mode
        deployment_mode = DeploymentMode(
            os.getenv('VRIN_DEPLOYMENT_MODE', 'centralized')
        )
        
        # Database configuration
        db_provider = DatabaseProvider(
            os.getenv('VRIN_DATABASE_PROVIDER', 'neptune')
        )
        
        database_config = DatabaseConfig(
            provider=db_provider,
            endpoint=os.getenv('VRIN_DATABASE_ENDPOINT'),
            port=int(os.getenv('VRIN_DATABASE_PORT', '8182')),
            region=os.getenv('VRIN_DATABASE_REGION', 'us-east-1'),
            credentials={
                'access_key': os.getenv('VRIN_DATABASE_ACCESS_KEY'),
                'secret_key': os.getenv('VRIN_DATABASE_SECRET_KEY'),
                'account_key': os.getenv('AZURE_COSMOS_KEY'),  # For Cosmos DB
            }
        )
        
        # LLM configuration
        llm_provider = LLMProvider(
            os.getenv('VRIN_LLM_PROVIDER', 'openai')
        )
        
        llm_config = LLMConfig(
            provider=llm_provider,
            model=os.getenv('VRIN_LLM_MODEL', 'gpt-4o-mini'),
            api_key=os.getenv('OPENAI_API_KEY') or os.getenv('AZURE_OPENAI_KEY'),
            endpoint=os.getenv('AZURE_OPENAI_ENDPOINT'),
            temperature=float(os.getenv('VRIN_LLM_TEMPERATURE', '0.1')),
            max_tokens=int(os.getenv('VRIN_LLM_MAX_TOKENS', '2000'))
        )
        
        # Network configuration (for hybrid/distributed deployments)
        network_config = None
        if deployment_mode != DeploymentMode.CENTRALIZED:
            network_config = NetworkConfig(
                vpc_id=os.getenv('VRIN_VPC_ID'),
                subnet_ids=os.getenv('VRIN_SUBNET_IDS', '').split(',') if os.getenv('VRIN_SUBNET_IDS') else None,
                security_group_ids=os.getenv('VRIN_SECURITY_GROUPS', '').split(',') if os.getenv('VRIN_SECURITY_GROUPS') else None,
                private_link_endpoint=os.getenv('VRIN_PRIVATE_LINK_ENDPOINT'),
                vpn_connection={
                    'gateway_id': os.getenv('VRIN_VPN_GATEWAY_ID'),
                    'connection_id': os.getenv('VRIN_VPN_CONNECTION_ID')
                } if os.getenv('VRIN_VPN_GATEWAY_ID') else None
            )
            
        # Security configuration
        security_config = SecurityConfig(
            encryption_at_rest=os.getenv('VRIN_ENCRYPT_AT_REST', 'true').lower() == 'true',
            encryption_in_transit=os.getenv('VRIN_ENCRYPT_IN_TRANSIT', 'true').lower() == 'true',
            customer_managed_keys={
                'kms_key_id': os.getenv('VRIN_KMS_KEY_ID'),
                'key_vault_url': os.getenv('AZURE_KEY_VAULT_URL')
            } if os.getenv('VRIN_KMS_KEY_ID') or os.getenv('AZURE_KEY_VAULT_URL') else None,
            audit_logging=os.getenv('VRIN_AUDIT_LOGGING', 'true').lower() == 'true',
            data_residency_region=os.getenv('VRIN_DATA_RESIDENCY_REGION'),
            compliance_standards=os.getenv('VRIN_COMPLIANCE_STANDARDS', '').split(',') if os.getenv('VRIN_COMPLIANCE_STANDARDS') else None
        )
        
        return VRINConfig(
            deployment_mode=deployment_mode,
            database=database_config,
            llm=llm_config,
            network=network_config,
            security=security_config,
            user_id=os.getenv('VRIN_USER_ID'),
            organization_id=os.getenv('VRIN_ORGANIZATION_ID')
        )
        
    @staticmethod
    def create_centralized_config(api_key: str, user_id: Optional[str] = None) -> VRINConfig:
        """Create configuration for centralized (free tier) deployment."""
        return VRINConfig(
            deployment_mode=DeploymentMode.CENTRALIZED,
            database=DatabaseConfig(
                provider=DatabaseProvider.NEPTUNE,
                endpoint="dev-vrin-neptune.cluster-ciqklfj1k1gd.us-east-1.neptune.amazonaws.com",
                port=8182,
                region="us-east-1"
            ),
            llm=LLMConfig(
                provider=LLMProvider.OPENAI,
                api_key=api_key,
                model="gpt-4o-mini"
            ),
            security=SecurityConfig(),
            user_id=user_id
        )
        
    @staticmethod 
    def create_hybrid_aws_config(
        neptune_endpoint: str,
        vpc_id: str,
        subnet_ids: list,
        user_id: Optional[str] = None,
        organization_id: Optional[str] = None,
        vrin_openai_proxy_endpoint: str = "https://thuiu23t0c.execute-api.us-east-1.amazonaws.com/dev/openai-proxy"
    ) -> VRINConfig:
        """Create configuration for hybrid AWS deployment (customer Neptune, VRIN OpenAI proxy)."""
        return VRINConfig(
            deployment_mode=DeploymentMode.HYBRID,
            database=DatabaseConfig(
                provider=DatabaseProvider.NEPTUNE,
                endpoint=neptune_endpoint,
                port=8182,
                region="us-east-1"
            ),
            llm=LLMConfig(
                provider=LLMProvider.OPENAI,
                endpoint=vrin_openai_proxy_endpoint,  # Use VRIN's OpenAI proxy
                model="gpt-4o-mini"
            ),
            network=NetworkConfig(
                vpc_id=vpc_id,
                subnet_ids=subnet_ids
            ),
            security=SecurityConfig(
                encryption_at_rest=True,
                encryption_in_transit=True,
                audit_logging=True
            ),
            user_id=user_id,
            organization_id=organization_id
        )
        
    @staticmethod
    def create_hybrid_azure_config(
        cosmos_account: str,
        cosmos_key: str,
        user_id: Optional[str] = None,
        organization_id: Optional[str] = None,
        vrin_openai_proxy_endpoint: str = "https://thuiu23t0c.execute-api.us-east-1.amazonaws.com/dev/openai-proxy"
    ) -> VRINConfig:
        """Create configuration for hybrid Azure deployment (customer Cosmos DB, VRIN OpenAI proxy)."""
        return VRINConfig(
            deployment_mode=DeploymentMode.HYBRID,
            database=DatabaseConfig(
                provider=DatabaseProvider.COSMOS_DB,
                endpoint=f"{cosmos_account}.gremlin.cosmos.azure.com",
                port=443,
                region="eastus",
                credentials={
                    'account_name': cosmos_account,
                    'account_key': cosmos_key
                }
            ),
            llm=LLMConfig(
                provider=LLMProvider.OPENAI,
                endpoint=vrin_openai_proxy_endpoint,  # Use VRIN's OpenAI proxy
                model="gpt-4o-mini"
            ),
            security=SecurityConfig(
                encryption_at_rest=True,
                encryption_in_transit=True,
                audit_logging=True,
                data_residency_region="eastus"
            ),
            user_id=user_id,
            organization_id=organization_id
        )
        
    @staticmethod 
    def create_open_source_config(
        janusgraph_endpoint: str,
        user_id: Optional[str] = None,
        vrin_openai_proxy_endpoint: str = "https://thuiu23t0c.execute-api.us-east-1.amazonaws.com/dev/openai-proxy"
    ) -> VRINConfig:
        """Create configuration for open source deployment (JanusGraph + VRIN OpenAI proxy)."""
        return VRINConfig(
            deployment_mode=DeploymentMode.DISTRIBUTED,
            database=DatabaseConfig(
                provider=DatabaseProvider.JANUSGRAPH,
                endpoint=janusgraph_endpoint,
                port=8182,
                additional_params={
                    'storage_backend': 'berkeleyje',
                    'index_backend': 'elasticsearch'
                }
            ),
            llm=LLMConfig(
                provider=LLMProvider.OPENAI,
                endpoint=vrin_openai_proxy_endpoint,  # Use VRIN's OpenAI proxy
                model="gpt-4o-mini"
            ),
            security=SecurityConfig(
                encryption_at_rest=False,  # Depends on JanusGraph setup
                encryption_in_transit=True,
                audit_logging=False
            ),
            user_id=user_id
        )


# Global config manager instance
_config_manager = None

def get_config_manager() -> ConfigManager:
    """Get global config manager instance."""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager


def get_config() -> VRINConfig:
    """Get current VRIN configuration."""
    return get_config_manager().get_config()


def set_config(config: VRINConfig) -> bool:
    """Set VRIN configuration."""
    return get_config_manager().save_config(config)


# Factory function for VPC-isolated deployments
def create_vpc_isolated_config(
    neptune_endpoint: str,
    openai_api_key: str,
    vpc_id: str,
    subnet_ids: List[str],
    security_group_ids: List[str],
    connectivity_type: str = "PrivateLink",
    region: str = "us-east-1",
    organization_id: Optional[str] = None,
    user_id: Optional[str] = None
) -> VRINConfig:
    """Create configuration for VPC-isolated enterprise deployment."""
    
    return VRINConfig(
        deployment_mode=DeploymentMode.HYBRID,
        database=DatabaseConfig(
            provider=DatabaseProvider.NEPTUNE,
            endpoint=neptune_endpoint,
            port=8182,
            region=region
        ),
        llm=LLMConfig(
            provider=LLMProvider.OPENAI,
            api_key=openai_api_key,
            model="gpt-4o-mini"
        ),
        network=NetworkConfig(
            vpc_id=vpc_id,
            subnet_ids=subnet_ids,
            security_group_ids=security_group_ids
        ),
        security=SecurityConfig(
            encryption_at_rest=True,
            encryption_in_transit=True,
            audit_logging=True,
            data_residency_region=region
        ),
        user_id=user_id,
        organization_id=organization_id,
        additional_config={
            'connectivity_type': connectivity_type,
            'vpc_isolation_enabled': True,
            'private_subnets_only': True,
            'region': region
        }
    )