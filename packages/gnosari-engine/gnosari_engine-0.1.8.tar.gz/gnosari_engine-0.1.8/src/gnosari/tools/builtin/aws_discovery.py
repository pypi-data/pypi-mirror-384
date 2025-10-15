"""
AWS Resource Discovery Tool - Using OpenAI Agents SDK FunctionTool

This tool allows agents to discover AWS resources across multiple services,
including EC2, S3, RDS, Lambda, IAM, and many others. It provides detailed
information about resources and can discover unknown resources via the
Resource Groups Tagging API.
"""

import logging
import asyncio
import json
import boto3
from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field
from agents import RunContextWrapper, FunctionTool
from ...tools.interfaces import SyncTool


class AWSDiscoveryArgs(BaseModel):
    """Arguments for the AWS resource discovery tool."""
    services: Optional[List[str]] = Field(
        default=None, 
        description="List of AWS services to discover (e.g., ['ec2', 's3', 'rds']). If None, discovers all supported services"
    )
    region: Optional[str] = Field(
        default="us-east-1", 
        description="AWS region to query (default: us-east-1)"
    )
    profile: Optional[str] = Field(
        default=None, 
        description="AWS profile name to use for authentication"
    )
    resource_types: Optional[List[str]] = Field(
        default=None,
        description="Specific resource types to discover (e.g., ['instances', 'buckets', 'functions'])"
    )
    include_cost_estimates: bool = Field(
        default=False, 
        description="Include rough cost estimates for discovered resources"
    )
    include_generic_discovery: bool = Field(
        default=True,
        description="Include generic resource discovery via Resource Groups Tagging API for unknown resources"
    )
    output_format: str = Field(
        default="summary", 
        description="Output format: 'summary', 'detailed', or 'json'"
    )
    
    class Config:
        extra = "forbid"


class AWSResourceDiscovery:
    """AWS Resource Discovery implementation."""
    
    def __init__(self, profile_name: str = None, region: str = 'us-east-1'):
        """Initialize AWS session and clients."""
        try:
            if profile_name:
                self.session = boto3.Session(profile_name=profile_name)
            else:
                self.session = boto3.Session()
            
            self.region = region
            self.account_id = self._get_account_id()
            self.resources = {}
            self.logger = logging.getLogger(__name__)
            
        except Exception as e:
            self.logger.error(f"Error initializing AWS session: {e}")
            raise
    
    def _get_account_id(self) -> str:
        """Get current AWS account ID."""
        sts = self.session.client('sts')
        return sts.get_caller_identity()['Account']
    
    def discover_ec2_resources(self):
        """Discover EC2 resources with detailed information."""
        ec2 = self.session.client('ec2', region_name=self.region)
        resources = {}
        
        # EC2 Instances
        try:
            response = ec2.describe_instances()
            instances = []
            for reservation in response['Reservations']:
                for instance in reservation['Instances']:
                    instance_details = {
                        'InstanceId': instance['InstanceId'],
                        'InstanceType': instance['InstanceType'],
                        'State': instance['State']['Name'],
                        'LaunchTime': instance.get('LaunchTime', '').isoformat() if instance.get('LaunchTime') else '',
                        'Platform': instance.get('Platform', 'Linux/Unix'),
                        'VpcId': instance.get('VpcId', ''),
                        'SubnetId': instance.get('SubnetId', ''),
                        'PrivateIpAddress': instance.get('PrivateIpAddress', ''),
                        'PublicIpAddress': instance.get('PublicIpAddress', ''),
                        'SecurityGroups': [sg['GroupId'] for sg in instance.get('SecurityGroups', [])],
                        'Tags': {tag['Key']: tag['Value'] for tag in instance.get('Tags', [])}
                    }
                    instances.append(instance_details)
            resources['instances'] = instances
        except Exception as e:
            resources['instances'] = f"Error: {e}"
        
        # Security Groups
        try:
            response = ec2.describe_security_groups()
            security_groups = []
            for sg in response['SecurityGroups']:
                sg_details = {
                    'GroupId': sg['GroupId'],
                    'GroupName': sg['GroupName'],
                    'Description': sg['Description'],
                    'VpcId': sg.get('VpcId', ''),
                    'Tags': {tag['Key']: tag['Value'] for tag in sg.get('Tags', [])}
                }
                security_groups.append(sg_details)
            resources['security_groups'] = security_groups
        except Exception as e:
            resources['security_groups'] = f"Error: {e}"
        
        # VPCs
        try:
            response = ec2.describe_vpcs()
            vpcs = []
            for vpc in response['VPCs']:
                vpc_details = {
                    'VpcId': vpc['VpcId'],
                    'CidrBlock': vpc['CidrBlock'],
                    'State': vpc['State'],
                    'IsDefault': vpc['IsDefault'],
                    'Tags': {tag['Key']: tag['Value'] for tag in vpc.get('Tags', [])}
                }
                vpcs.append(vpc_details)
            resources['vpcs'] = vpcs
        except Exception as e:
            resources['vpcs'] = f"Error: {e}"
        
        # EBS Volumes
        try:
            response = ec2.describe_volumes()
            volumes = []
            for volume in response['Volumes']:
                volume_details = {
                    'VolumeId': volume['VolumeId'],
                    'VolumeType': volume['VolumeType'],
                    'Size': volume['Size'],
                    'State': volume['State'],
                    'AvailabilityZone': volume['AvailabilityZone'],
                    'Encrypted': volume.get('Encrypted', False),
                    'Tags': {tag['Key']: tag['Value'] for tag in volume.get('Tags', [])}
                }
                volumes.append(volume_details)
            resources['volumes'] = volumes
        except Exception as e:
            resources['volumes'] = f"Error: {e}"
        
        self.resources['ec2'] = resources
    
    def discover_s3_resources(self):
        """Discover S3 resources."""
        s3 = self.session.client('s3')
        resources = {}
        
        try:
            response = s3.list_buckets()
            buckets = []
            for bucket in response['Buckets']:
                bucket_info = {
                    'Name': bucket['Name'],
                    'CreationDate': bucket['CreationDate'].isoformat(),
                }
                
                # Get bucket region
                try:
                    location = s3.get_bucket_location(Bucket=bucket['Name'])
                    bucket_info['Region'] = location['LocationConstraint'] or 'us-east-1'
                except Exception:
                    bucket_info['Region'] = 'Unknown'
                
                # Get bucket tags
                try:
                    tags_response = s3.get_bucket_tagging(Bucket=bucket['Name'])
                    bucket_info['Tags'] = {tag['Key']: tag['Value'] for tag in tags_response.get('TagSet', [])}
                except Exception:
                    bucket_info['Tags'] = {}
                
                buckets.append(bucket_info)
            
            resources['buckets'] = buckets
        except Exception as e:
            resources['buckets'] = f"Error: {e}"
        
        self.resources['s3'] = resources
    
    def discover_rds_resources(self):
        """Discover RDS resources."""
        rds = self.session.client('rds', region_name=self.region)
        resources = {}
        
        # DB Instances
        try:
            response = rds.describe_db_instances()
            resources['db_instances'] = [
                {
                    'DBInstanceIdentifier': db['DBInstanceIdentifier'],
                    'DBInstanceClass': db['DBInstanceClass'],
                    'Engine': db['Engine'],
                    'EngineVersion': db['EngineVersion'],
                    'DBInstanceStatus': db['DBInstanceStatus'],
                    'AllocatedStorage': db.get('AllocatedStorage', 0),
                    'MultiAZ': db.get('MultiAZ', False),
                    'VpcId': db.get('DBSubnetGroup', {}).get('VpcId', '') if db.get('DBSubnetGroup') else ''
                }
                for db in response['DBInstances']
            ]
        except Exception as e:
            resources['db_instances'] = f"Error: {e}"
        
        self.resources['rds'] = resources
    
    def discover_lambda_resources(self):
        """Discover Lambda resources."""
        lambda_client = self.session.client('lambda', region_name=self.region)
        resources = {}
        
        try:
            response = lambda_client.list_functions()
            resources['functions'] = [
                {
                    'FunctionName': func['FunctionName'],
                    'Runtime': func.get('Runtime', ''),
                    'Handler': func.get('Handler', ''),
                    'CodeSize': func.get('CodeSize', 0),
                    'LastModified': func.get('LastModified', ''),
                    'Timeout': func.get('Timeout', 0),
                    'MemorySize': func.get('MemorySize', 0),
                    'Role': func.get('Role', '')
                }
                for func in response['Functions']
            ]
        except Exception as e:
            resources['functions'] = f"Error: {e}"
        
        self.resources['lambda'] = resources
    
    def discover_iam_resources(self):
        """Discover IAM resources."""
        iam = self.session.client('iam')
        resources = {}
        
        # Users
        try:
            response = iam.list_users()
            resources['users'] = [
                {
                    'UserName': user['UserName'],
                    'UserId': user['UserId'],
                    'CreateDate': user['CreateDate'].isoformat(),
                    'Path': user['Path']
                }
                for user in response['Users']
            ]
        except Exception as e:
            resources['users'] = f"Error: {e}"
        
        # Roles
        try:
            response = iam.list_roles()
            resources['roles'] = [
                {
                    'RoleName': role['RoleName'],
                    'RoleId': role['RoleId'],
                    'CreateDate': role['CreateDate'].isoformat(),
                    'Path': role['Path']
                }
                for role in response['Roles']
            ]
        except Exception as e:
            resources['roles'] = f"Error: {e}"
        
        self.resources['iam'] = resources
    
    def discover_generic_resources(self):
        """Discover any resources not covered by specific service methods using Resource Groups Tagging API."""
        try:
            client = self.session.client('resourcegroupstaggingapi', region_name=self.region)
            
            # Get all resources with their tags
            paginator = client.get_paginator('get_resources')
            all_resources = []
            
            for page in paginator.paginate():
                all_resources.extend(page.get('ResourceTagMappingList', []))
            
            # Organize by service
            services_found = {}
            for resource in all_resources:
                arn = resource.get('ResourceARN', '')
                if arn:
                    # Extract service name from ARN
                    arn_parts = arn.split(':')
                    if len(arn_parts) >= 3:
                        service = arn_parts[2]
                        if service not in services_found:
                            services_found[service] = []
                        services_found[service].append({
                            'ResourceARN': arn,
                            'Tags': {tag['Key']: tag['Value'] for tag in resource.get('Tags', [])}
                        })
            
            # Store discovered resources
            self.resources['generic_discovery'] = {
                'total_resources_found': len(all_resources),
                'services_discovered': list(services_found.keys()),
                'resources_by_service': services_found
            }
            
        except Exception as e:
            self.resources['generic_discovery'] = f"Error: {e}"
    
    def add_cost_estimation(self):
        """Add cost estimation for discovered resources."""
        cost_estimates = {}
        
        # EC2 Cost Estimation (simplified)
        if 'ec2' in self.resources and isinstance(self.resources['ec2'], dict):
            ec2_cost = 0
            if 'instances' in self.resources['ec2'] and isinstance(self.resources['ec2']['instances'], list):
                instance_costs = {
                    't2.micro': 0.0116, 't2.small': 0.023, 't2.medium': 0.0464,
                    't3.micro': 0.0104, 't3.small': 0.0208, 't3.medium': 0.0416,
                    'm5.large': 0.096, 'm5.xlarge': 0.192, 'm5.2xlarge': 0.384,
                    'c5.large': 0.085, 'c5.xlarge': 0.17, 'c5.2xlarge': 0.34
                }
                for instance in self.resources['ec2']['instances']:
                    if isinstance(instance, dict) and instance.get('State') == 'running':
                        instance_type = instance.get('InstanceType', '')
                        hourly_cost = instance_costs.get(instance_type, 0.1)
                        ec2_cost += hourly_cost * 24 * 30  # Monthly estimate
            cost_estimates['ec2_monthly_estimate'] = round(ec2_cost, 2)
        
        # S3 Cost Estimation (simplified)
        if 's3' in self.resources and isinstance(self.resources['s3'], dict):
            if 'buckets' in self.resources['s3'] and isinstance(self.resources['s3']['buckets'], list):
                bucket_count = len(self.resources['s3']['buckets'])
                cost_estimates['s3_monthly_estimate_min'] = round(bucket_count * 1, 2)
        
        self.resources['cost_estimates'] = cost_estimates
    
    def discover_resources(self, services: List[str] = None, include_cost_estimates: bool = False, 
                          include_generic_discovery: bool = True):
        """Discover resources from specified or all supported services."""
        all_services = {
            'ec2': self.discover_ec2_resources,
            's3': self.discover_s3_resources,
            'rds': self.discover_rds_resources,
            'lambda': self.discover_lambda_resources,
            'iam': self.discover_iam_resources
        }
        
        services_to_discover = services or list(all_services.keys())
        
        for service_name in services_to_discover:
            if service_name in all_services:
                try:
                    all_services[service_name]()
                except Exception as e:
                    self.resources[service_name] = f"Error: {e}"
        
        if include_generic_discovery:
            self.discover_generic_resources()
        
        if include_cost_estimates:
            self.add_cost_estimation()
    
    def format_summary(self) -> str:
        """Format a summary of discovered resources."""
        lines = [
            f"AWS Resource Discovery Summary",
            f"Account ID: {self.account_id}",
            f"Region: {self.region}",
            f"Discovery Time: {datetime.now().isoformat()}",
            "-" * 40
        ]
        
        total_resources = 0
        for service, data in self.resources.items():
            if service == 'cost_estimates' or service == 'generic_discovery':
                continue
            
            lines.append(f"\n{service.upper()} Resources:")
            if isinstance(data, dict):
                for resource_type, resource_list in data.items():
                    if isinstance(resource_list, list):
                        count = len(resource_list)
                        total_resources += count
                        lines.append(f"  {resource_type}: {count}")
                    else:
                        lines.append(f"  {resource_type}: {resource_list}")
            else:
                lines.append(f"  {data}")
        
        if 'generic_discovery' in self.resources:
            generic = self.resources['generic_discovery']
            if isinstance(generic, dict):
                lines.append(f"\nGeneric Discovery:")
                lines.append(f"  Total resources found: {generic.get('total_resources_found', 0)}")
                services_found = generic.get('services_discovered', [])
                if services_found:
                    lines.append(f"  Services discovered: {', '.join(services_found[:10])}")
        
        if 'cost_estimates' in self.resources:
            lines.append(f"\nCost Estimates (Monthly USD):")
            cost_data = self.resources['cost_estimates']
            if isinstance(cost_data, dict):
                for service, cost in cost_data.items():
                    if isinstance(cost, (int, float)) and cost > 0:
                        lines.append(f"  {service}: ${cost}")
        
        lines.append(f"\nTotal resources discovered: {total_resources}")
        return "\n".join(lines)


class AWSDiscoveryTool(SyncTool):
    """AWS Resource Discovery Tool for AI agents."""
    
    def __init__(self, default_profile: str = None, default_region: str = "us-east-1", 
                 default_include_cost_estimates: bool = False, 
                 default_include_generic_discovery: bool = True,
                 default_output_format: str = "summary"):
        """Initialize the AWS discovery tool.
        
        Args:
            default_profile: Default AWS profile to use for authentication
            default_region: Default AWS region for resource discovery
            default_include_cost_estimates: Default setting for cost estimation
            default_include_generic_discovery: Default setting for generic discovery
            default_output_format: Default output format ("summary", "detailed", "json")
        """
        super().__init__(
            name="aws_discovery",
            description="Discover AWS resources across multiple services with detailed information",
            input_schema=AWSDiscoveryArgs
        )
        
        # Store default configuration
        self.default_profile = default_profile
        self.default_region = default_region
        self.default_include_cost_estimates = default_include_cost_estimates
        self.default_include_generic_discovery = default_include_generic_discovery
        self.default_output_format = default_output_format
        
        self.logger = logging.getLogger(__name__)
        
        # Create the FunctionTool
        self.tool = FunctionTool(
            name=self.name,
            description=self.description,
            params_json_schema=AWSDiscoveryArgs.model_json_schema(),
            on_invoke_tool=self._run_discovery
        )
    
    async def _run_discovery(self, ctx: RunContextWrapper[Any], args: str) -> str:
        """Execute the AWS resource discovery.
        
        Args:
            ctx: Run context wrapper
            args: JSON string containing AWSDiscoveryArgs
            
        Returns:
            AWS resource discovery results as string
        """
        try:
            # Parse arguments
            parsed_args = AWSDiscoveryArgs.model_validate_json(args)
            
            # Use tool defaults if not specified in call
            profile = parsed_args.profile or self.default_profile
            region = parsed_args.region or self.default_region
            include_cost_estimates = parsed_args.include_cost_estimates if hasattr(parsed_args, 'include_cost_estimates') and parsed_args.include_cost_estimates is not None else self.default_include_cost_estimates
            include_generic_discovery = parsed_args.include_generic_discovery if hasattr(parsed_args, 'include_generic_discovery') and parsed_args.include_generic_discovery is not None else self.default_include_generic_discovery
            output_format = parsed_args.output_format or self.default_output_format
            
            self.logger.info(f"🔍 AWS DISCOVERY STARTED - Profile: {profile or 'default'}, Region: {region}")
            
            # Initialize discovery
            discovery = AWSResourceDiscovery(
                profile_name=profile,
                region=region
            )
            
            # Discover resources
            discovery.discover_resources(
                services=parsed_args.services,
                include_cost_estimates=include_cost_estimates,
                include_generic_discovery=include_generic_discovery
            )
            
            # Format output based on requested format
            if output_format == 'json':
                result = json.dumps(discovery.resources, indent=2, default=str)
            elif output_format == 'detailed':
                result = json.dumps(discovery.resources, indent=2, default=str)
            else:  # summary
                result = discovery.format_summary()
            
            self.logger.info("✅ AWS DISCOVERY COMPLETED")
            return result
                    
        except Exception as e:
            self.logger.error(f"❌ AWS DISCOVERY FAILED: {str(e)}")
            return f"Error discovering AWS resources: {str(e)}"
    
    def get_tool(self) -> FunctionTool:
        """Get the FunctionTool instance.
        
        Returns:
            FunctionTool instance
        """
        return self.tool


def get_default_aws_discovery_tool() -> FunctionTool:
    """Get a default AWS discovery tool instance.
    
    Returns:
        FunctionTool instance
    """
    return AWSDiscoveryTool().get_tool()