"""
Network configuration and VPC isolation for VRIN enterprise deployments.

Supports:
- VPC isolation with private subnets
- PrivateLink endpoints for AWS services
- VPN and Direct Connect connectivity
- Cross-region networking
- Network security group management
"""

import json
import logging
from enum import Enum
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Any, Union

logger = logging.getLogger(__name__)


class ConnectivityType(Enum):
    """Types of network connectivity for hybrid deployments."""
    INTERNET = "internet"                    # Public internet (not recommended for production)
    VPC_PEERING = "vpc_peering"             # AWS VPC peering
    PRIVATE_LINK = "private_link"           # AWS PrivateLink endpoints
    VPN_CONNECTION = "vpn_connection"       # Site-to-Site VPN
    DIRECT_CONNECT = "direct_connect"       # AWS Direct Connect
    TRANSIT_GATEWAY = "transit_gateway"     # AWS Transit Gateway
    EXPRESSROUTE = "expressroute"           # Azure ExpressRoute
    CLOUD_INTERCONNECT = "cloud_interconnect"  # Google Cloud Interconnect


class NetworkTier(Enum):
    """Network security tiers."""
    PUBLIC = "public"           # Public subnets with internet gateway
    PRIVATE = "private"         # Private subnets with NAT gateway
    ISOLATED = "isolated"       # Isolated subnets with no internet access
    DATABASE = "database"       # Database-specific subnets


@dataclass
class SubnetConfig:
    """Configuration for a VPC subnet."""
    subnet_id: str
    cidr_block: str
    availability_zone: str
    tier: NetworkTier
    name: Optional[str] = None
    route_table_id: Optional[str] = None
    
    
@dataclass
class SecurityGroupRule:
    """Network security group rule."""
    protocol: str  # tcp, udp, icmp, -1 (all)
    from_port: int
    to_port: int
    source_type: str  # cidr, security_group, prefix_list
    source_value: str
    description: Optional[str] = None
    

@dataclass
class SecurityGroupConfig:
    """Security group configuration."""
    group_id: str
    name: str
    description: str
    vpc_id: str
    ingress_rules: List[SecurityGroupRule]
    egress_rules: List[SecurityGroupRule]
    tags: Optional[Dict[str, str]] = None


@dataclass
class VPCEndpointConfig:
    """VPC endpoint configuration for PrivateLink."""
    service_name: str  # e.g., com.amazonaws.us-east-1.s3
    vpc_endpoint_id: Optional[str] = None
    subnet_ids: Optional[List[str]] = None
    security_group_ids: Optional[List[str]] = None
    policy_document: Optional[Dict[str, Any]] = None
    route_table_ids: Optional[List[str]] = None  # For gateway endpoints


@dataclass 
class VPNConnectionConfig:
    """VPN connection configuration."""
    vpn_connection_id: str
    customer_gateway_id: str
    vpn_gateway_id: str
    transit_gateway_id: Optional[str] = None
    static_routes: Optional[List[str]] = None
    bgp_asn: Optional[int] = None
    

@dataclass
class DirectConnectConfig:
    """Direct Connect configuration."""
    connection_id: str
    vlan_id: int
    bgp_asn: int
    customer_address: str
    amazon_address: str
    address_family: str = "ipv4"  # ipv4 or ipv6
    

@dataclass
class NetworkConfig:
    """Complete network configuration for enterprise deployments."""
    vpc_id: str
    region: str
    subnets: List[SubnetConfig]
    security_groups: List[SecurityGroupConfig]
    connectivity_type: ConnectivityType
    
    # Optional connectivity configurations
    vpc_endpoints: Optional[List[VPCEndpointConfig]] = None
    vpn_connection: Optional[VPNConnectionConfig] = None
    direct_connect: Optional[DirectConnectConfig] = None
    
    # Cross-region configuration
    peer_regions: Optional[List[str]] = None
    transit_gateway_id: Optional[str] = None
    
    # DNS and routing
    enable_dns_hostnames: bool = True
    enable_dns_support: bool = True
    custom_dns_servers: Optional[List[str]] = None
    
    # Monitoring and logging
    vpc_flow_logs_enabled: bool = True
    flow_logs_destination: str = "cloudwatch"  # cloudwatch, s3
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'NetworkConfig':
        """Create from dictionary."""
        # Convert enums
        data['connectivity_type'] = ConnectivityType(data['connectivity_type'])
        
        # Convert subnets
        if 'subnets' in data:
            data['subnets'] = [
                SubnetConfig(**subnet) if isinstance(subnet, dict) 
                else subnet for subnet in data['subnets']
            ]
        
        # Convert security groups
        if 'security_groups' in data:
            security_groups = []
            for sg in data['security_groups']:
                if isinstance(sg, dict):
                    # Convert rules
                    if 'ingress_rules' in sg:
                        sg['ingress_rules'] = [
                            SecurityGroupRule(**rule) if isinstance(rule, dict) 
                            else rule for rule in sg['ingress_rules']
                        ]
                    if 'egress_rules' in sg:
                        sg['egress_rules'] = [
                            SecurityGroupRule(**rule) if isinstance(rule, dict) 
                            else rule for rule in sg['egress_rules']
                        ]
                    security_groups.append(SecurityGroupConfig(**sg))
                else:
                    security_groups.append(sg)
            data['security_groups'] = security_groups
        
        return cls(**data)


class NetworkConfigManager:
    """Manages network configurations for different deployment scenarios."""
    
    @staticmethod
    def create_basic_vpc_config(
        vpc_id: str, 
        region: str,
        private_subnet_ids: List[str],
        connectivity_type: ConnectivityType = ConnectivityType.PRIVATE_LINK
    ) -> NetworkConfig:
        """Create basic VPC configuration for hybrid deployment."""
        
        # Create basic private subnets
        subnets = []
        for i, subnet_id in enumerate(private_subnet_ids):
            subnet = SubnetConfig(
                subnet_id=subnet_id,
                cidr_block=f"10.0.{i+1}.0/24",  # Placeholder, should be detected
                availability_zone=f"{region}{chr(97+i)}",  # a, b, c...
                tier=NetworkTier.PRIVATE,
                name=f"vrin-private-subnet-{i+1}"
            )
            subnets.append(subnet)
        
        # Create basic security groups
        lambda_sg = SecurityGroupConfig(
            group_id="sg-lambda-placeholder",
            name="vrin-lambda-sg",
            description="Security group for VRIN Lambda functions",
            vpc_id=vpc_id,
            ingress_rules=[
                SecurityGroupRule(
                    protocol="tcp",
                    from_port=443,
                    to_port=443,
                    source_type="cidr",
                    source_value="10.0.0.0/16",
                    description="HTTPS from VPC"
                )
            ],
            egress_rules=[
                SecurityGroupRule(
                    protocol="-1",
                    from_port=-1,
                    to_port=-1,
                    source_type="cidr",
                    source_value="0.0.0.0/0",
                    description="All outbound traffic"
                )
            ]
        )
        
        database_sg = SecurityGroupConfig(
            group_id="sg-database-placeholder",
            name="vrin-database-sg", 
            description="Security group for VRIN database services",
            vpc_id=vpc_id,
            ingress_rules=[
                SecurityGroupRule(
                    protocol="tcp",
                    from_port=8182,
                    to_port=8182,
                    source_type="security_group",
                    source_value="sg-lambda-placeholder",
                    description="Neptune from Lambda"
                ),
                SecurityGroupRule(
                    protocol="tcp",
                    from_port=443,
                    to_port=443,
                    source_type="security_group",
                    source_value="sg-lambda-placeholder", 
                    description="OpenSearch from Lambda"
                )
            ],
            egress_rules=[]  # No outbound for database
        )
        
        return NetworkConfig(
            vpc_id=vpc_id,
            region=region,
            subnets=subnets,
            security_groups=[lambda_sg, database_sg],
            connectivity_type=connectivity_type,
            vpc_flow_logs_enabled=True,
            flow_logs_destination="cloudwatch"
        )
    
    @staticmethod
    def create_privatelink_config(
        vpc_id: str,
        region: str,
        subnet_ids: List[str]
    ) -> NetworkConfig:
        """Create configuration with PrivateLink endpoints."""
        
        base_config = NetworkConfigManager.create_basic_vpc_config(
            vpc_id, region, subnet_ids, ConnectivityType.PRIVATE_LINK
        )
        
        # Add VPC endpoints for AWS services
        vpc_endpoints = [
            # S3 Gateway endpoint
            VPCEndpointConfig(
                service_name=f"com.amazonaws.{region}.s3",
                route_table_ids=["rtb-placeholder"]  # Should be detected
            ),
            
            # Lambda interface endpoint
            VPCEndpointConfig(
                service_name=f"com.amazonaws.{region}.lambda",
                subnet_ids=subnet_ids,
                security_group_ids=["sg-lambda-placeholder"]
            ),
            
            # API Gateway interface endpoint
            VPCEndpointConfig(
                service_name=f"com.amazonaws.{region}.execute-api",
                subnet_ids=subnet_ids,
                security_group_ids=["sg-lambda-placeholder"]
            ),
            
            # Neptune (if available in region)
            VPCEndpointConfig(
                service_name=f"com.amazonaws.{region}.neptune-db",
                subnet_ids=subnet_ids,
                security_group_ids=["sg-database-placeholder"]
            ),
            
            # OpenSearch
            VPCEndpointConfig(
                service_name=f"com.amazonaws.{region}.es",
                subnet_ids=subnet_ids,
                security_group_ids=["sg-database-placeholder"]
            )
        ]
        
        base_config.vpc_endpoints = vpc_endpoints
        return base_config
    
    @staticmethod
    def create_vpn_config(
        vpc_id: str,
        region: str,
        subnet_ids: List[str],
        customer_gateway_id: str,
        vpn_gateway_id: str,
        static_routes: List[str] = None
    ) -> NetworkConfig:
        """Create configuration with VPN connectivity."""
        
        base_config = NetworkConfigManager.create_basic_vpc_config(
            vpc_id, region, subnet_ids, ConnectivityType.VPN_CONNECTION
        )
        
        # Add VPN configuration
        vpn_config = VPNConnectionConfig(
            vpn_connection_id="vpn-placeholder",  # Should be provided
            customer_gateway_id=customer_gateway_id,
            vpn_gateway_id=vpn_gateway_id,
            static_routes=static_routes or ["192.168.0.0/16"]
        )
        
        base_config.vpn_connection = vpn_config
        return base_config
    
    @staticmethod
    def create_cross_region_config(
        primary_vpc_id: str,
        primary_region: str,
        subnet_ids: List[str],
        peer_regions: List[str],
        transit_gateway_id: str = None
    ) -> NetworkConfig:
        """Create cross-region network configuration."""
        
        base_config = NetworkConfigManager.create_privatelink_config(
            primary_vpc_id, primary_region, subnet_ids
        )
        
        base_config.peer_regions = peer_regions
        base_config.transit_gateway_id = transit_gateway_id
        base_config.connectivity_type = ConnectivityType.TRANSIT_GATEWAY
        
        return base_config
    
    @staticmethod
    def validate_network_config(config: NetworkConfig) -> List[str]:
        """Validate network configuration and return list of issues."""
        issues = []
        
        # Basic validation
        if not config.vpc_id.startswith('vpc-'):
            issues.append("VPC ID should start with 'vpc-'")
        
        if not config.subnets:
            issues.append("At least one subnet must be configured")
        
        # Subnet validation
        for subnet in config.subnets:
            if not subnet.subnet_id.startswith('subnet-'):
                issues.append(f"Subnet ID {subnet.subnet_id} should start with 'subnet-'")
        
        # Security group validation
        for sg in config.security_groups:
            if not sg.group_id.startswith('sg-'):
                issues.append(f"Security group ID {sg.group_id} should start with 'sg-'")
        
        # Connectivity-specific validation
        if config.connectivity_type == ConnectivityType.VPN_CONNECTION:
            if not config.vpn_connection:
                issues.append("VPN connection configuration required for VPN connectivity")
        
        if config.connectivity_type == ConnectivityType.DIRECT_CONNECT:
            if not config.direct_connect:
                issues.append("Direct Connect configuration required for DX connectivity")
        
        if config.connectivity_type == ConnectivityType.PRIVATE_LINK:
            if not config.vpc_endpoints:
                issues.append("VPC endpoints required for PrivateLink connectivity")
        
        return issues


# Pre-defined network configurations for common scenarios
COMMON_NETWORK_CONFIGS = {
    "basic_private": {
        "name": "Basic Private Subnet",
        "description": "Simple private subnet configuration with NAT gateway",
        "connectivity_type": ConnectivityType.INTERNET,
        "recommended_for": ["Development", "Testing"]
    },
    
    "privatelink_production": {
        "name": "PrivateLink Production",
        "description": "Production-ready PrivateLink configuration with VPC endpoints",
        "connectivity_type": ConnectivityType.PRIVATE_LINK,
        "recommended_for": ["Production", "High Security"]
    },
    
    "vpn_hybrid": {
        "name": "VPN Hybrid Connectivity", 
        "description": "Site-to-Site VPN for hybrid cloud connectivity",
        "connectivity_type": ConnectivityType.VPN_CONNECTION,
        "recommended_for": ["Hybrid Cloud", "On-premise Integration"]
    },
    
    "direct_connect_enterprise": {
        "name": "Direct Connect Enterprise",
        "description": "AWS Direct Connect for dedicated network connection",
        "connectivity_type": ConnectivityType.DIRECT_CONNECT,
        "recommended_for": ["Enterprise", "High Bandwidth", "Low Latency"]
    }
}