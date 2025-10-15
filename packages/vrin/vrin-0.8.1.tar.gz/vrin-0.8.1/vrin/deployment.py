"""
VRIN enterprise deployment manager for VPC isolation and hybrid connectivity.

Handles deployment scenarios:
1. Basic VPC isolation
2. PrivateLink connectivity
3. VPN hybrid connectivity  
4. Direct Connect enterprise
5. Cross-region deployments
"""

import json
import logging
import boto3
import time
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum

from .network import NetworkConfig, NetworkConfigManager, ConnectivityType
from .config import VRINConfig, DeploymentMode

logger = logging.getLogger(__name__)


class DeploymentStatus(Enum):
    """Deployment status values."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLBACK_IN_PROGRESS = "rollback_in_progress"
    ROLLBACK_COMPLETED = "rollback_completed"


@dataclass
class DeploymentResult:
    """Result of a deployment operation."""
    status: DeploymentStatus
    deployment_id: str
    resources_created: Dict[str, str]
    errors: List[str]
    start_time: float
    end_time: Optional[float] = None
    
    @property
    def duration(self) -> Optional[float]:
        """Get deployment duration in seconds."""
        if self.end_time:
            return self.end_time - self.start_time
        return None


class VPCDeploymentManager:
    """Manages VPC isolation deployments for VRIN enterprise customers."""
    
    def __init__(self, region: str = 'us-east-1', profile: str = None):
        """Initialize deployment manager."""
        self.region = region
        self.session = boto3.Session(profile_name=profile) if profile else boto3.Session()
        
        # AWS clients
        self.cf_client = self.session.client('cloudformation', region_name=region)
        self.ec2_client = self.session.client('ec2', region_name=region)
        self.lambda_client = self.session.client('lambda', region_name=region)
        
        self.deployments: Dict[str, DeploymentResult] = {}
        
    def deploy_vpc_isolation(
        self, 
        organization_id: str,
        environment: str,
        network_config: NetworkConfig,
        template_path: str = None
    ) -> DeploymentResult:
        """Deploy VPC isolation infrastructure."""
        
        deployment_id = f"vrin-vpc-{organization_id}-{environment}-{int(time.time())}"
        
        deployment = DeploymentResult(
            status=DeploymentStatus.PENDING,
            deployment_id=deployment_id,
            resources_created={},
            errors=[],
            start_time=time.time()
        )
        
        self.deployments[deployment_id] = deployment
        
        try:
            deployment.status = DeploymentStatus.IN_PROGRESS
            
            # Load CloudFormation template
            template_content = self._load_template(template_path or 'template-vpc-isolation.yaml')
            
            # Prepare parameters
            parameters = self._prepare_parameters(organization_id, environment, network_config)
            
            # Create CloudFormation stack
            stack_name = f"vrin-vpc-{organization_id}-{environment}"
            
            logger.info(f"Creating CloudFormation stack: {stack_name}")
            
            response = self.cf_client.create_stack(
                StackName=stack_name,
                TemplateBody=template_content,
                Parameters=parameters,
                Capabilities=['CAPABILITY_IAM', 'CAPABILITY_NAMED_IAM'],
                Tags=[
                    {'Key': 'Environment', 'Value': environment},
                    {'Key': 'OrganizationId', 'Value': organization_id},
                    {'Key': 'Purpose', 'Value': 'VRIN-VPC-Isolation'},
                    {'Key': 'DeploymentId', 'Value': deployment_id}
                ]
            )
            
            # Wait for stack creation
            stack_id = response['StackId']
            deployment.resources_created['cloudformation_stack'] = stack_id
            
            logger.info(f"Waiting for stack creation: {stack_name}")
            
            # Poll stack status
            stack_status = self._wait_for_stack_completion(stack_name)
            
            if stack_status == 'CREATE_COMPLETE':
                # Get stack outputs
                outputs = self._get_stack_outputs(stack_name)
                deployment.resources_created.update(outputs)
                
                deployment.status = DeploymentStatus.COMPLETED
                deployment.end_time = time.time()
                
                logger.info(f"VPC deployment completed: {deployment_id}")
                
            else:
                deployment.status = DeploymentStatus.FAILED
                deployment.errors.append(f"CloudFormation stack failed: {stack_status}")
                deployment.end_time = time.time()
                
        except Exception as e:
            deployment.status = DeploymentStatus.FAILED
            deployment.errors.append(str(e))
            deployment.end_time = time.time()
            logger.error(f"VPC deployment failed: {str(e)}")
            
        return deployment
        
    def deploy_privatelink_connectivity(
        self,
        organization_id: str,
        environment: str,
        vpc_id: str,
        subnet_ids: List[str]
    ) -> DeploymentResult:
        """Deploy PrivateLink VPC endpoints for secure connectivity."""
        
        deployment_id = f"vrin-privatelink-{organization_id}-{environment}-{int(time.time())}"
        
        deployment = DeploymentResult(
            status=DeploymentStatus.IN_PROGRESS,
            deployment_id=deployment_id,
            resources_created={},
            errors=[],
            start_time=time.time()
        )
        
        try:
            # Create VPC endpoints for AWS services
            endpoints_config = [
                {
                    'service': 's3',
                    'type': 'Gateway',
                    'route_tables': self._get_route_tables(vpc_id)
                },
                {
                    'service': 'lambda', 
                    'type': 'Interface',
                    'subnets': subnet_ids
                },
                {
                    'service': 'execute-api',
                    'type': 'Interface', 
                    'subnets': subnet_ids
                },
                {
                    'service': 'secretsmanager',
                    'type': 'Interface',
                    'subnets': subnet_ids
                }
            ]
            
            for endpoint_config in endpoints_config:
                try:
                    endpoint_id = self._create_vpc_endpoint(
                        vpc_id,
                        endpoint_config,
                        organization_id,
                        environment
                    )
                    
                    deployment.resources_created[f"vpc_endpoint_{endpoint_config['service']}"] = endpoint_id
                    
                except Exception as e:
                    deployment.errors.append(f"Failed to create {endpoint_config['service']} endpoint: {str(e)}")
            
            if not deployment.errors:
                deployment.status = DeploymentStatus.COMPLETED
            else:
                deployment.status = DeploymentStatus.FAILED
                
            deployment.end_time = time.time()
            
        except Exception as e:
            deployment.status = DeploymentStatus.FAILED
            deployment.errors.append(str(e))
            deployment.end_time = time.time()
            
        self.deployments[deployment_id] = deployment
        return deployment
        
    def configure_lambda_vpc(
        self,
        function_names: List[str],
        vpc_id: str,
        subnet_ids: List[str],
        security_group_ids: List[str]
    ) -> DeploymentResult:
        """Configure Lambda functions to run in customer VPC."""
        
        deployment_id = f"vrin-lambda-vpc-{int(time.time())}"
        
        deployment = DeploymentResult(
            status=DeploymentStatus.IN_PROGRESS,
            deployment_id=deployment_id,
            resources_created={},
            errors=[],
            start_time=time.time()
        )
        
        try:
            vpc_config = {
                'SubnetIds': subnet_ids,
                'SecurityGroupIds': security_group_ids
            }
            
            for function_name in function_names:
                try:
                    logger.info(f"Configuring VPC for Lambda function: {function_name}")
                    
                    response = self.lambda_client.update_function_configuration(
                        FunctionName=function_name,
                        VpcConfig=vpc_config
                    )
                    
                    deployment.resources_created[f"lambda_vpc_{function_name}"] = response['FunctionArn']
                    
                    # Wait for function update to complete
                    waiter = self.lambda_client.get_waiter('function_updated')
                    waiter.wait(FunctionName=function_name)
                    
                except Exception as e:
                    deployment.errors.append(f"Failed to configure VPC for {function_name}: {str(e)}")
            
            if not deployment.errors:
                deployment.status = DeploymentStatus.COMPLETED
            else:
                deployment.status = DeploymentStatus.FAILED
                
            deployment.end_time = time.time()
            
        except Exception as e:
            deployment.status = DeploymentStatus.FAILED
            deployment.errors.append(str(e))
            deployment.end_time = time.time()
            
        self.deployments[deployment_id] = deployment
        return deployment
        
    def validate_network_connectivity(
        self,
        vpc_id: str,
        subnet_ids: List[str],
        connectivity_type: ConnectivityType
    ) -> Dict[str, Any]:
        """Validate network connectivity for VRIN services."""
        
        results = {
            'overall_status': 'unknown',
            'checks': [],
            'recommendations': []
        }
        
        try:
            # Basic VPC validation
            vpc_info = self.ec2_client.describe_vpcs(VpcIds=[vpc_id])
            if vpc_info['Vpcs']:
                results['checks'].append({
                    'name': 'VPC Exists',
                    'status': 'passed',
                    'details': f"VPC {vpc_id} found"
                })
            else:
                results['checks'].append({
                    'name': 'VPC Exists',
                    'status': 'failed',
                    'details': f"VPC {vpc_id} not found"
                })
                
            # Subnet validation
            subnet_info = self.ec2_client.describe_subnets(SubnetIds=subnet_ids)
            available_subnets = len(subnet_info['Subnets'])
            
            results['checks'].append({
                'name': 'Subnet Availability',
                'status': 'passed' if available_subnets == len(subnet_ids) else 'failed',
                'details': f"{available_subnets}/{len(subnet_ids)} subnets available"
            })
            
            # Connectivity-specific checks
            if connectivity_type == ConnectivityType.PRIVATE_LINK:
                self._validate_privatelink_connectivity(vpc_id, results)
            elif connectivity_type == ConnectivityType.VPN_CONNECTION:
                self._validate_vpn_connectivity(vpc_id, results)
                
            # Overall status
            failed_checks = [c for c in results['checks'] if c['status'] == 'failed']
            if not failed_checks:
                results['overall_status'] = 'healthy'
            elif len(failed_checks) <= 1:
                results['overall_status'] = 'warning'
            else:
                results['overall_status'] = 'unhealthy'
                
        except Exception as e:
            results['overall_status'] = 'error'
            results['checks'].append({
                'name': 'Validation Error',
                'status': 'failed',
                'details': str(e)
            })
            
        return results
        
    def get_deployment_status(self, deployment_id: str) -> Optional[DeploymentResult]:
        """Get status of a deployment."""
        return self.deployments.get(deployment_id)
        
    def list_deployments(self, organization_id: str = None) -> List[DeploymentResult]:
        """List all deployments, optionally filtered by organization."""
        deployments = list(self.deployments.values())
        
        if organization_id:
            # Filter by organization ID in deployment ID
            deployments = [d for d in deployments if organization_id in d.deployment_id]
            
        return sorted(deployments, key=lambda x: x.start_time, reverse=True)
        
    def cleanup_deployment(self, deployment_id: str) -> bool:
        """Clean up resources from a deployment."""
        deployment = self.deployments.get(deployment_id)
        if not deployment:
            return False
            
        try:
            # Delete CloudFormation stack if exists
            if 'cloudformation_stack' in deployment.resources_created:
                stack_id = deployment.resources_created['cloudformation_stack']
                # Extract stack name from ARN
                stack_name = stack_id.split('/')[-2]
                
                logger.info(f"Deleting CloudFormation stack: {stack_name}")
                self.cf_client.delete_stack(StackName=stack_name)
                
                # Wait for deletion
                self._wait_for_stack_completion(stack_name, 'DELETE_COMPLETE')
                
            return True
            
        except Exception as e:
            logger.error(f"Failed to cleanup deployment {deployment_id}: {str(e)}")
            return False
            
    # Private helper methods
    def _load_template(self, template_path: str) -> str:
        """Load CloudFormation template."""
        import os
        
        if not os.path.isabs(template_path):
            # Relative to infrastructure/yaml directory
            base_path = os.path.join(os.path.dirname(__file__), '..', 'infrastructure', 'yaml')
            template_path = os.path.join(base_path, template_path)
            
        with open(template_path, 'r') as f:
            return f.read()
            
    def _prepare_parameters(
        self, 
        organization_id: str, 
        environment: str, 
        network_config: NetworkConfig
    ) -> List[Dict[str, str]]:
        """Prepare CloudFormation parameters."""
        
        parameters = [
            {'ParameterKey': 'Environment', 'ParameterValue': environment},
            {'ParameterKey': 'OrganizationId', 'ParameterValue': organization_id},
            {'ParameterKey': 'ConnectivityType', 'ParameterValue': network_config.connectivity_type.value},
        ]
        
        # Add VPC CIDR if available
        if hasattr(network_config, 'vpc_cidr'):
            parameters.append({
                'ParameterKey': 'VpcCidr',
                'ParameterValue': network_config.vpc_cidr
            })
            
        return parameters
        
    def _wait_for_stack_completion(self, stack_name: str, expected_status: str = 'CREATE_COMPLETE') -> str:
        """Wait for CloudFormation stack to reach completion."""
        
        max_wait = 1800  # 30 minutes
        wait_time = 0
        
        while wait_time < max_wait:
            try:
                response = self.cf_client.describe_stacks(StackName=stack_name)
                stack = response['Stacks'][0]
                status = stack['StackStatus']
                
                if status in [expected_status, 'CREATE_COMPLETE', 'UPDATE_COMPLETE', 'DELETE_COMPLETE']:
                    return status
                elif status in ['CREATE_FAILED', 'UPDATE_FAILED', 'DELETE_FAILED', 'ROLLBACK_COMPLETE']:
                    return status
                    
                time.sleep(30)
                wait_time += 30
                
            except Exception as e:
                logger.error(f"Error checking stack status: {str(e)}")
                break
                
        return 'TIMEOUT'
        
    def _get_stack_outputs(self, stack_name: str) -> Dict[str, str]:
        """Get CloudFormation stack outputs."""
        try:
            response = self.cf_client.describe_stacks(StackName=stack_name)
            stack = response['Stacks'][0]
            
            outputs = {}
            for output in stack.get('Outputs', []):
                outputs[output['OutputKey']] = output['OutputValue']
                
            return outputs
            
        except Exception as e:
            logger.error(f"Error getting stack outputs: {str(e)}")
            return {}
            
    def _get_route_tables(self, vpc_id: str) -> List[str]:
        """Get route table IDs for a VPC."""
        try:
            response = self.ec2_client.describe_route_tables(
                Filters=[{'Name': 'vpc-id', 'Values': [vpc_id]}]
            )
            
            return [rt['RouteTableId'] for rt in response['RouteTables']]
            
        except Exception as e:
            logger.error(f"Error getting route tables: {str(e)}")
            return []
            
    def _create_vpc_endpoint(
        self,
        vpc_id: str,
        endpoint_config: Dict[str, Any],
        organization_id: str,
        environment: str
    ) -> str:
        """Create a VPC endpoint."""
        
        service_name = f"com.amazonaws.{self.region}.{endpoint_config['service']}"
        
        params = {
            'VpcId': vpc_id,
            'ServiceName': service_name,
            'VpcEndpointType': endpoint_config['type'],
            'TagSpecifications': [{
                'ResourceType': 'vpc-endpoint',
                'Tags': [
                    {'Key': 'Name', 'Value': f"{environment}-vrin-{endpoint_config['service']}-endpoint"},
                    {'Key': 'OrganizationId', 'Value': organization_id},
                    {'Key': 'Environment', 'Value': environment}
                ]
            }]
        }
        
        if endpoint_config['type'] == 'Interface':
            params['SubnetIds'] = endpoint_config['subnets']
            params['PrivateDnsEnabled'] = True
        elif endpoint_config['type'] == 'Gateway':
            params['RouteTableIds'] = endpoint_config['route_tables']
            
        response = self.ec2_client.create_vpc_endpoint(**params)
        return response['VpcEndpoint']['VpcEndpointId']
        
    def _validate_privatelink_connectivity(self, vpc_id: str, results: Dict[str, Any]):
        """Validate PrivateLink connectivity."""
        try:
            # Check for VPC endpoints
            response = self.ec2_client.describe_vpc_endpoints(
                Filters=[{'Name': 'vpc-id', 'Values': [vpc_id]}]
            )
            
            endpoints = response['VpcEndpoints']
            required_services = ['s3', 'lambda', 'execute-api']
            
            for service in required_services:
                service_name = f"com.amazonaws.{self.region}.{service}"
                endpoint_exists = any(ep['ServiceName'] == service_name for ep in endpoints)
                
                results['checks'].append({
                    'name': f'{service.upper()} VPC Endpoint',
                    'status': 'passed' if endpoint_exists else 'failed',
                    'details': f"VPC endpoint for {service} {'exists' if endpoint_exists else 'missing'}"
                })
                
        except Exception as e:
            results['checks'].append({
                'name': 'PrivateLink Validation',
                'status': 'failed',
                'details': str(e)
            })
            
    def _validate_vpn_connectivity(self, vpc_id: str, results: Dict[str, Any]):
        """Validate VPN connectivity."""
        try:
            # Check for VPN connections
            response = self.ec2_client.describe_vpn_connections(
                Filters=[{'Name': 'vpc-id', 'Values': [vpc_id]}]
            )
            
            vpn_connections = response['VpnConnections']
            active_vpns = [vpn for vpn in vpn_connections if vpn['State'] == 'available']
            
            results['checks'].append({
                'name': 'VPN Connectivity',
                'status': 'passed' if active_vpns else 'failed',
                'details': f"{len(active_vpns)} active VPN connections found"
            })
            
        except Exception as e:
            results['checks'].append({
                'name': 'VPN Validation', 
                'status': 'failed',
                'details': str(e)
            })