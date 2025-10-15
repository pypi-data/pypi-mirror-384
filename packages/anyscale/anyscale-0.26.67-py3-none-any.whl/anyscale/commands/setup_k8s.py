"""
Kubernetes Cloud Setup Command

This module provides a streamlined command for setting up Anyscale on Kubernetes clusters.
It handles infrastructure provisioning, cloud registration, and operator installation.
"""

from dataclasses import dataclass
import json
import os
import re
import subprocess
from typing import Any, Dict, List, Optional

import click
import yaml

from anyscale.cli_logger import BlockLogger
from anyscale.client.openapi_client.models import (
    AWSConfig,
    CloudDeployment,
    CloudProviders,
    ComputeStack,
    KubernetesConfig as OpenAPIKubernetesConfig,
    ObjectStorage,
)
from anyscale.controllers.cloud_controller import CloudController
from anyscale.controllers.kubernetes_verifier import (
    KubernetesCloudDeploymentVerifier,
    KubernetesConfig,
)
from anyscale.shared_anyscale_utils.conf import ANYSCALE_CORS_ORIGIN, ANYSCALE_HOST


@dataclass
class ClusterInfo:
    """Information about the target Kubernetes cluster."""

    context: str
    namespace: str
    provider: str
    region: str
    cluster_name: str
    project_id: Optional[str] = None
    cluster_arn: Optional[str] = None
    oidc_provider: Optional[str] = None
    cluster_location: Optional[str] = None
    workload_identity_pool: Optional[str] = None
    cluster_version: Optional[str] = None


@dataclass
class InfrastructureResources:
    """Resources created during infrastructure setup."""

    bucket_name: str
    iam_role_arn: str
    region: str
    project_id: Optional[str] = None


class KubernetesCloudSetupCommand:
    """Command to setup Kubernetes cloud."""

    def __init__(self, logger: Optional[BlockLogger] = None, debug: bool = False):
        self.log = logger or BlockLogger()
        self.cloud_controller = CloudController(log=self.log)
        self.skip_confirmation = False
        self.debug = debug or os.environ.get("ANYSCALE_DEBUG") == "1"

    def run(  # noqa: PLR0913
        self,
        provider: str,
        region: str,
        name: str,
        cluster_name: str,
        namespace: str,
        project_id: Optional[str],
        functional_verify: bool,
        yes: bool,
        values_file: Optional[str] = None,
    ) -> None:
        """
        Main entry point for Kubernetes cloud setup.

        Args:
            provider: Cloud provider (aws, gcp)
            region: AWS/GCP region
            name: Name for the Anyscale cloud
            cluster_name: Kubernetes cluster name/context
            namespace: Namespace for the Anyscale operator
            project_id: GCP project ID (required for GCP)
            functional_verify: Whether to run functional verification
            yes: Skip confirmation prompts
            values_file: Optional custom path for Helm values file
        """
        self.log.open_block(
            "Setup", f"Setting up Kubernetes cloud '{name}' on {provider.upper()}"
        )

        # Set confirmation flag
        self.skip_confirmation = yes

        try:
            # Step 0: Check required CLI tools are installed
            self._check_required_tools(provider)

            # Step 1: Prompt for namespace BEFORE infrastructure setup
            # This is needed because the IAM role trust relationship depends on the namespace
            final_namespace = self._prompt_for_namespace(
                namespace, skip_confirmation=yes
            )

            # Step 2: Discover and validate cluster
            cluster_info = self._discover_cluster(
                cluster_name, final_namespace, provider, region, project_id
            )

            # Step 3: Set up cloud infrastructure
            infrastructure = self._setup_infrastructure(
                provider, region, name, cluster_info
            )

            # Step 4: Register cloud with Anyscale
            cloud_id = self._register_cloud(
                name, provider, region, infrastructure, cluster_info
            )

            # Step 5: Install Anyscale operator
            self._install_operator(
                cloud_id,
                provider,
                region,
                final_namespace,
                infrastructure,
                values_file,
            )

            # Step 6: Verify installation
            if functional_verify:
                self._verify_installation(cloud_id, final_namespace, cluster_info)

            self.log.close_block("Setup")
            self.log.info(f"Kubernetes cloud '{name}' setup completed successfully!")
        except Exception:  # noqa: BLE001
            self.log.close_block("Setup")
            raise

    def _debug(self, *msg: str) -> None:
        """Log debug messages only when debug mode is enabled."""
        if self.debug:
            self.log.debug(*msg)

    def _check_required_tools(self, provider: str) -> None:
        """Check that required CLI tools are installed."""
        # Common tools required for all providers
        required_tools = ["kubectl", "helm"]

        # Provider-specific tools
        if provider == "aws":
            required_tools.append("aws")
        elif provider == "gcp":
            required_tools.extend(["gcloud", "gsutil"])

        self._debug(f"Checking for required tools: {', '.join(required_tools)}")

        missing_tools = []
        for tool in required_tools:
            if not self._check_command_available(tool):
                missing_tools.append(tool)

        if missing_tools:
            error_msg = f"Missing required CLI tools: {', '.join(missing_tools)}\n\n"
            raise click.ClickException(error_msg.rstrip())

        self.log.info(
            f"Required CLI tools are installed ({', '.join(required_tools)})",
            block_label="Setup",
        )

    def _check_command_available(self, command: str) -> bool:
        """Check if a command is available in the system PATH."""
        try:
            result = subprocess.run(
                ["which", command], capture_output=True, text=True, check=False
            )
            return result.returncode == 0
        except Exception:  # noqa: BLE001
            return False

    def _discover_cluster(
        self,
        cluster_name: str,
        namespace: str,
        provider: str,
        region: str,
        project_id: Optional[str],  # noqa: ARG002
    ) -> ClusterInfo:
        """Discover and validate the target Kubernetes cluster using cloud provider APIs."""
        self.log.info(
            f"Discovering {provider.upper()} cluster: {cluster_name}",
            block_label="Setup",
        )

        if provider == "aws":
            return self._discover_aws_cluster(cluster_name, namespace, region)
        elif provider == "gcp":
            raise click.ClickException(
                "GCP support is not yet implemented. Please use AWS for now."
            )
        else:
            raise click.ClickException(f"Unsupported provider: {provider}")

    def _discover_aws_cluster(
        self, cluster_name: str, namespace: str, region: str
    ) -> ClusterInfo:
        """Discover AWS EKS cluster details and configure kubeconfig."""
        try:
            self._debug(f"Fetching EKS cluster info for {cluster_name} in {region}...")
            cluster_info = self._get_eks_cluster_info(cluster_name, region)
            self._debug(f"EKS Cluster ARN: {cluster_info.get('arn', 'Unknown')}")
            self._debug(
                f"EKS Cluster Version: {cluster_info.get('version', 'Unknown')}"
            )
        except Exception as e:  # noqa: BLE001
            self.log.error(f"Failed to get EKS cluster info: {e}")
            raise click.ClickException(
                f"Failed to discover EKS cluster {cluster_name}: {e}"
            )

        try:
            self._debug("Fetching OIDC provider information...")
            oidc_provider = self._get_eks_oidc_provider(cluster_name, region)
            self._debug(f"OIDC Provider: {oidc_provider}")
        except Exception as e:  # noqa: BLE001
            self.log.error(f"Failed to get OIDC provider: {e}")
            raise click.ClickException(
                f"Failed to get OIDC provider for cluster {cluster_name}: {e}"
            )

        try:
            self._debug("Configuring kubeconfig for EKS cluster...")
            self._configure_aws_kubeconfig(cluster_name, region)
        except Exception as e:  # noqa: BLE001
            self.log.error(f"Failed to configure kubeconfig: {e}")
            raise click.ClickException(
                f"Failed to configure kubeconfig for EKS cluster: {e}"
            )

        try:
            self._debug("Verifying kubeconfig configuration...")
            self._verify_kubeconfig()
            current_context = self._get_current_kubectl_context()
            self.log.info(f"Cluster discovered: {current_context}", block_label="Setup")
        except Exception as e:  # noqa: BLE001
            self.log.error(f"Failed to verify kubeconfig: {e}")
            raise click.ClickException(f"Failed to verify kubeconfig: {e}")

        return ClusterInfo(
            context=current_context,
            namespace=namespace,
            provider="aws",
            region=region,
            cluster_name=cluster_name,
            cluster_arn=cluster_info.get("arn"),
            oidc_provider=oidc_provider,
            cluster_version=cluster_info.get("version"),
        )

    def _setup_infrastructure(
        self, provider: str, region: str, name: str, cluster_info: ClusterInfo,
    ) -> InfrastructureResources:
        """Set up cloud infrastructure (S3/GCS bucket, IAM roles, etc.)."""
        self.log.info(
            f"Setting up {provider.upper()} infrastructure...", block_label="Setup"
        )

        if provider == "aws":
            return self._setup_aws_infrastructure(region, name, cluster_info)
        elif provider == "gcp":
            raise click.ClickException(
                "GCP support is not yet implemented. Please use AWS for now."
            )
        else:
            raise click.ClickException(f"Unsupported provider: {provider}")

    def _setup_aws_infrastructure(  # noqa: PLR0912
        self, region: str, name: str, cluster_info: ClusterInfo,
    ) -> InfrastructureResources:
        """Set up AWS infrastructure for Kubernetes using CloudFormation."""
        try:
            import boto3

            from anyscale.utils.cloudformation_utils import CloudFormationUtils
        except ImportError as e:
            self.log.error(f"Failed to import required modules: {e}")
            raise click.ClickException(f"Failed to import required modules: {e}")

        try:
            # Generate a unique cloud ID
            cloud_id = f"k8s-{name}-{os.urandom(4).hex()}"
            stack_name = cloud_id.replace("_", "-").lower()
            self._debug(f"Generated cloud ID: {cloud_id}")
            self._debug(f"CloudFormation stack name: {stack_name}")
        except Exception as e:  # noqa: BLE001
            self.log.error(f"Failed to generate cloud ID: {e}")
            raise click.ClickException(f"Failed to generate cloud ID: {e}")

        try:
            # Generate CloudFormation template for Kubernetes setup with actual OIDC provider
            if not cluster_info.oidc_provider:
                raise click.ClickException(
                    "OIDC provider information not found. Please ensure the EKS cluster has OIDC provider enabled."
                )
            self._debug("Generating CloudFormation template...")
            self._debug(
                f"Using namespace: {cluster_info.namespace} with service account: anyscale-operator"
            )
            cfn_template_body = self._generate_aws_cloudformation_template(
                cloud_id, cluster_info.oidc_provider, cluster_info.namespace,
            )
            self._debug("CloudFormation template generated successfully")
        except Exception as e:  # noqa: BLE001
            self.log.error(f"Failed to generate CloudFormation template: {e}")
            raise click.ClickException(
                f"Failed to generate CloudFormation template: {e}"
            )

        try:
            self._debug("Preparing CloudFormation parameters...")
            parameters = [{"ParameterKey": "CloudID", "ParameterValue": cloud_id}]
            self._debug(f"Prepared {len(parameters)} CloudFormation parameters")
        except Exception as e:  # noqa: BLE001
            self.log.error(f"Failed to prepare CloudFormation parameters: {e}")
            raise click.ClickException(
                f"Failed to prepare CloudFormation parameters: {e}"
            )

        try:
            with self.log.indent():
                self.log.info(
                    "Creating CloudFormation stack (this may take a few minutes)...",
                    block_label="Setup",
                )
                boto3_session = boto3.Session(region_name=region)
                cfn_utils = CloudFormationUtils(self.log)
                cfn_utils.create_and_wait_for_stack(
                    stack_name=stack_name,
                    template_body=cfn_template_body,
                    parameters=parameters,
                    region=region,
                    boto3_session=boto3_session,
                    timeout_seconds=600,
                )
            self.log.info("CloudFormation stack created", block_label="Setup")
        except Exception as e:  # noqa: BLE001
            self.log.error(f"Failed to create CloudFormation stack: {e}")
            raise click.ClickException(f"Failed to create CloudFormation stack: {e}")

        try:
            self._debug("Retrieving CloudFormation stack outputs...")
            stack_outputs = cfn_utils.get_stack_outputs(
                stack_name, region, boto3_session
            )
            bucket_name = stack_outputs.get("S3BucketName", f"anyscale-{cloud_id}")
            iam_role_arn = stack_outputs.get("AnyscaleCrossAccountIAMRoleArn")

            if not iam_role_arn:
                raise click.ClickException(
                    "Failed to get IAM role ARN from CloudFormation stack"
                )

            self._debug(f"S3 Bucket: {bucket_name}")
            self._debug(f"IAM Role ARN: {iam_role_arn}")
        except Exception as e:  # noqa: BLE001
            self.log.error(f"Failed to get CloudFormation outputs: {e}")
            raise click.ClickException(f"Failed to get CloudFormation outputs: {e}")

        return InfrastructureResources(
            bucket_name=bucket_name, iam_role_arn=iam_role_arn, region=region
        )

    def _generate_aws_cloudformation_template(
        self, cloud_id: str, oidc_provider_arn: str, namespace: str,
    ) -> str:
        """Generate CloudFormation template for AWS Kubernetes setup."""
        # Extract OIDC provider URL from ARN for the condition
        # ARN format: arn:aws:iam::ACCOUNT:oidc-provider/oidc.eks.REGION.amazonaws.com/id/XXXXXX
        # We need: oidc.eks.REGION.amazonaws.com/id/XXXXXX
        if "oidc-provider/" not in oidc_provider_arn:
            raise click.ClickException(
                f"Invalid OIDC provider ARN format: {oidc_provider_arn}"
            )
        oidc_provider_url = oidc_provider_arn.split("oidc-provider/")[-1]

        service_account_name = "anyscale-operator"

        # Use ANYSCALE_CORS_ORIGIN from shared config
        # This respects the ANYSCALE_HOST environment variable
        allowed_origin = ANYSCALE_CORS_ORIGIN

        template = {
            "AWSTemplateFormatVersion": "2010-09-09",
            "Description": f"Anyscale Kubernetes Cloud Infrastructure for {cloud_id}",
            "Parameters": {
                "CloudID": {
                    "Type": "String",
                    "Description": "Cloud ID for resource naming",
                }
            },
            "Resources": {
                "AnyscaleBucket": {
                    "Type": "AWS::S3::Bucket",
                    "Properties": {
                        "BucketName": {"Fn::Sub": "anyscale-${CloudID}"},
                        "VersioningConfiguration": {"Status": "Enabled"},
                        "PublicAccessBlockConfiguration": {
                            "BlockPublicAcls": True,
                            "BlockPublicPolicy": True,
                            "IgnorePublicAcls": True,
                            "RestrictPublicBuckets": True,
                        },
                        "CorsConfiguration": {
                            "CorsRules": [
                                {
                                    "AllowedHeaders": ["*"],
                                    "AllowedMethods": [
                                        "GET",
                                        "PUT",
                                        "POST",
                                        "HEAD",
                                        "DELETE",
                                    ],
                                    "AllowedOrigins": [allowed_origin],
                                    "MaxAge": 3600,
                                }
                            ]
                        },
                    },
                },
                "AnyscaleOperatorRole": {
                    "Type": "AWS::IAM::Role",
                    "Properties": {
                        "RoleName": {"Fn::Sub": "${CloudID}-anyscale-operator-role"},
                        "AssumeRolePolicyDocument": {
                            "Version": "2012-10-17",
                            "Statement": [
                                {
                                    "Effect": "Allow",
                                    "Principal": {"Federated": oidc_provider_arn},
                                    "Action": "sts:AssumeRoleWithWebIdentity",
                                    "Condition": {
                                        "StringEquals": {
                                            f"{oidc_provider_url}:sub": f"system:serviceaccount:{namespace}:{service_account_name}"
                                        }
                                    },
                                }
                            ],
                        },
                        "Policies": [
                            {
                                "PolicyName": "AnyscaleS3AccessPolicy",
                                "PolicyDocument": {
                                    "Version": "2012-10-17",
                                    "Statement": [
                                        {
                                            "Effect": "Allow",
                                            "Action": [
                                                "s3:GetObject",
                                                "s3:PutObject",
                                                "s3:DeleteObject",
                                                "s3:ListBucket",
                                            ],
                                            "Resource": [
                                                {
                                                    "Fn::GetAtt": [
                                                        "AnyscaleBucket",
                                                        "Arn",
                                                    ]
                                                },
                                                {"Fn::Sub": "${AnyscaleBucket.Arn}/*"},
                                            ],
                                        }
                                    ],
                                },
                            }
                        ],
                    },
                },
            },
            "Outputs": {
                "S3BucketName": {
                    "Value": {"Ref": "AnyscaleBucket"},
                    "Description": "Name of the S3 bucket",
                },
                "AnyscaleCrossAccountIAMRoleArn": {
                    "Value": {"Fn::GetAtt": ["AnyscaleOperatorRole", "Arn"]},
                    "Description": "ARN of the Anyscale operator IAM role",
                },
            },
        }

        return json.dumps(template, indent=2)

    def _get_eks_cluster_info(self, cluster_name: str, region: str) -> Dict[str, Any]:
        """Get EKS cluster information using AWS CLI."""
        try:
            result = subprocess.run(
                [
                    "aws",
                    "eks",
                    "describe-cluster",
                    "--name",
                    cluster_name,
                    "--region",
                    region,
                ],
                capture_output=True,
                text=True,
                check=True,
            )
            cluster_data = json.loads(result.stdout)
            return cluster_data.get("cluster", {})
        except subprocess.CalledProcessError as e:
            raise click.ClickException(f"Failed to get EKS cluster info: {e.stderr}")

    def _get_eks_availability_zones(self, cluster_name: str, region: str) -> List[str]:
        """Get availability zones where the EKS cluster's subnets are located."""
        try:
            cluster_info = self._get_eks_cluster_info(cluster_name, region)
            subnet_ids = cluster_info.get("resourcesVpcConfig", {}).get("subnetIds", [])

            if not subnet_ids:
                self._debug(
                    "No subnets found in cluster info, falling back to default zones"
                )
                return [region + "a", region + "b", region + "c"]

            # Get subnet details to find their availability zones
            result = subprocess.run(
                [
                    "aws",
                    "ec2",
                    "describe-subnets",
                    "--subnet-ids",
                    *subnet_ids,
                    "--region",
                    region,
                    "--query",
                    "Subnets[*].AvailabilityZone",
                    "--output",
                    "json",
                ],
                capture_output=True,
                text=True,
                check=True,
            )

            zones = json.loads(result.stdout)
            # Remove duplicates and sort
            unique_zones = sorted(set(zones))

            if unique_zones:
                self._debug(f"Discovered availability zones: {', '.join(unique_zones)}")
                return unique_zones
            else:
                self._debug(
                    "No availability zones found, falling back to default zones"
                )
                return [region + "a", region + "b", region + "c"]

        except Exception as e:  # noqa: BLE001
            self._debug(f"Failed to get availability zones: {e}, using default zones")
            return [region + "a", region + "b", region + "c"]

    def _get_eks_oidc_provider(self, cluster_name: str, region: str) -> str:
        """Get EKS OIDC provider URL for IRSA."""
        cluster_info = self._get_eks_cluster_info(cluster_name, region)
        identity = cluster_info.get("identity", {})
        oidc_issuer = identity.get("oidc", {}).get("issuer", "")

        if not oidc_issuer:
            raise click.ClickException(
                "Could not find OIDC issuer for EKS cluster. IRSA setup requires OIDC provider."
            )

        # Extract OIDC provider ARN
        # OIDC issuer URL format: https://oidc.eks.region.amazonaws.com/id/EXAMPLED539D4633E53CE8D
        if "oidc.eks." in oidc_issuer and ".amazonaws.com/id/" in oidc_issuer:
            oidc_id = oidc_issuer.split("/id/")[-1]
            account_id = self._get_aws_account_id()
            oidc_provider_arn = f"arn:aws:iam::{account_id}:oidc-provider/oidc.eks.{region}.amazonaws.com/id/{oidc_id}"
            return oidc_provider_arn

        raise click.ClickException(
            f"Could not parse OIDC provider from issuer URL: {oidc_issuer}"
        )

    def _get_aws_account_id(self) -> str:
        """Get AWS account ID."""
        try:
            result = subprocess.run(
                [
                    "aws",
                    "sts",
                    "get-caller-identity",
                    "--query",
                    "Account",
                    "--output",
                    "text",
                ],
                capture_output=True,
                text=True,
                check=True,
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            raise click.ClickException(f"Failed to get AWS account ID: {e.stderr}")

    def _configure_aws_kubeconfig(self, cluster_name: str, region: str) -> None:
        """Configure kubeconfig for AWS EKS cluster."""
        self.log.info(f"Configuring kubeconfig for EKS cluster: {cluster_name}")

        try:
            subprocess.run(
                [
                    "aws",
                    "eks",
                    "update-kubeconfig",
                    "--region",
                    region,
                    "--name",
                    cluster_name,
                ],
                capture_output=True,
                text=True,
                check=True,
            )
            self.log.info("EKS kubeconfig configured successfully")
        except subprocess.CalledProcessError as e:
            raise click.ClickException(
                f"Failed to configure EKS kubeconfig: {e.stderr}"
            )

    def _verify_kubeconfig(self) -> None:
        """Verify that kubeconfig is working correctly."""
        self.log.info("Verifying kubeconfig configuration...")

        try:
            subprocess.run(
                ["kubectl", "cluster-info"], capture_output=True, text=True, check=True
            )
            self.log.info("Kubeconfig verification successful")
        except subprocess.CalledProcessError as e:
            raise click.ClickException(f"Kubeconfig verification failed: {e.stderr}")

    def _get_current_kubectl_context(self) -> str:
        """Get the current kubectl context."""
        try:
            result = subprocess.run(
                ["kubectl", "config", "current-context"],
                capture_output=True,
                text=True,
                check=True,
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            raise click.ClickException(
                f"Failed to get current kubectl context: {e.stderr}"
            )

    def _register_cloud(  # noqa: PLR0912
        self,
        name: str,
        provider: str,
        region: str,
        infrastructure: InfrastructureResources,
        cluster_info: ClusterInfo,
    ) -> str:
        """Register the cloud with Anyscale."""
        self.log.info("Registering cloud with Anyscale...", block_label="Setup")

        if provider == "aws":
            # Dynamically determine availability zones from the EKS cluster
            zones = self._get_eks_availability_zones(cluster_info.cluster_name, region)

            cloud_deployment = CloudDeployment(
                name=name,
                provider=CloudProviders.AWS,
                region=region,
                compute_stack=ComputeStack.K8S,
                object_storage=ObjectStorage(
                    bucket_name=infrastructure.bucket_name, region=region
                ),
                aws_config=AWSConfig(),
                kubernetes_config=OpenAPIKubernetesConfig(
                    anyscale_operator_iam_identity=infrastructure.iam_role_arn,
                    zones=zones,
                ),
            )
        else:
            raise click.ClickException(
                "GCP support is not yet implemented. Please use AWS for now."
            )

        # Register the cloud
        try:
            self._debug("Cloud deployment details:")
            self._debug(f"  Name: {cloud_deployment.name}")
            self._debug(f"  Provider: {cloud_deployment.provider}")
            self._debug(f"  Region: {cloud_deployment.region}")
            self._debug(f"  Compute Stack: {cloud_deployment.compute_stack}")
            self._debug(f"  Bucket Name: {cloud_deployment.object_storage.bucket_name}")
            self._debug(
                f"  IAM Identity: {cloud_deployment.kubernetes_config.anyscale_operator_iam_identity}"
            )
            if cloud_deployment.aws_config:
                self._debug("  AWS Config:")
                self._debug(
                    f"    IAM Role ID: {cloud_deployment.aws_config.anyscale_iam_role_id}"
                )

            # Temporarily suppress cloud controller logging to avoid Helm command output
            original_log_info = self.cloud_controller.log.info
            self.cloud_controller.log.info = lambda *_args, **_kwargs: None

            try:
                if provider == "aws":
                    self.log.info("Calling register_aws_cloud...")
                    self.cloud_controller.register_aws_cloud(
                        name=name,
                        cloud_resource=cloud_deployment,
                        functional_verify=None,
                        yes=True,
                        skip_verifications=True,
                        auto_add_user=True,
                    )
                else:
                    raise click.ClickException(
                        "GCP support is not yet implemented. Please use AWS for now."
                    )
            finally:
                # Restore the original log.info method
                self.cloud_controller.log.info = original_log_info

            self._debug("Cloud registration completed, fetching cloud ID...")
            clouds = (
                self.cloud_controller.api_client.list_clouds_api_v2_clouds_get().results
            )
            cloud = next((c for c in clouds if c.name == name), None)
            if not cloud:
                raise click.ClickException("Failed to find registered cloud")

            cloud_id = getattr(cloud, "id", None) or getattr(cloud, "cloud_id", None)
            if not cloud_id:
                raise click.ClickException(
                    "Failed to get cloud ID from registered cloud"
                )

            self.log.info(f"Cloud registered with ID: {cloud_id}", block_label="Setup")

            return cloud_id

        except Exception as e:  # noqa: BLE001
            self.log.error(f"Cloud registration failed with error: {e}")
            self.log.error(f"Error type: {type(e).__name__}")
            if hasattr(e, "response"):
                self.log.error(f"Response details: {getattr(e, 'response', 'N/A')}")
            if hasattr(e, "args"):
                self.log.error(f"Error args: {e.args}")
            import traceback

            self.log.error(f"Full traceback: {traceback.format_exc()}")
            raise click.ClickException(f"Failed to register cloud: {e}")

    def _install_operator(  # noqa: PLR0913
        self,
        cloud_id: str,
        provider: str,
        region: str,
        namespace: str,
        infrastructure: InfrastructureResources,
        values_file: Optional[str] = None,
    ) -> None:
        """Install the Anyscale operator using Helm."""
        self.log.info("Installing Anyscale operator...", block_label="Setup")

        # Get cloud resources to get the cloud resource ID
        cloud_resources = self.cloud_controller.get_decorated_cloud_resources(cloud_id)

        if not cloud_resources:
            raise click.ClickException("No cloud resources found")

        cloud_resource_id = cloud_resources[0].cloud_resource_id

        release_name = "anyscale-operator"

        # Generate Helm command and extract --set-string flags from it
        self._debug("Generating Helm command to extract parameters...")
        helm_command = self.cloud_controller._generate_helm_upgrade_command(  # noqa: SLF001
            provider=provider,
            cloud_deployment_id=cloud_resource_id,
            region=region,
            operator_iam_identity=infrastructure.iam_role_arn,
        )

        set_string_values = self._extract_set_string_values(helm_command)
        self._debug(f"Extracted {len(set_string_values)} --set-string parameters")

        values_file_path = self._generate_helm_values_file(
            provider=provider,
            cloud_deployment_id=cloud_resource_id,
            region=region,
            namespace=namespace,
            infrastructure=infrastructure,
            custom_path=values_file,
            additional_values=set_string_values,
        )

        # Build a simple Helm command that only uses the values file
        self._debug("Generating Helm command...")
        helm_command = (
            f"helm upgrade {release_name} anyscale/anyscale-operator "
            f"--values {values_file_path} "
            f"--namespace {namespace} "
            f"--create-namespace "
            f"--wait "
            f"-i"
        )

        self._execute_helm_command(helm_command)

    def _extract_set_string_values(self, helm_command: str) -> Dict[str, str]:
        """
        Extract all --set-string key=value pairs from a Helm command.

        Args:
            helm_command: The Helm command string to parse

        Returns:
            Dictionary of key-value pairs from --set-string flags
        """
        import re

        set_string_values = {}

        # Pattern to match --set-string key=value
        pattern = r"--set-string\s+(\S+?)=(\S+)"

        matches = re.findall(pattern, helm_command)
        for key, value in matches:
            set_string_values[key] = value

        return set_string_values

    def _prompt_for_namespace(
        self, default_namespace: str, skip_confirmation: bool = False
    ) -> str:
        """Prompt user for namespace confirmation."""
        final_namespace = default_namespace or "anyscale-operator"

        if skip_confirmation:
            self.log.info(f"Using namespace: {final_namespace}", block_label="Setup")
            return final_namespace

        self.log.info("Configuring Kubernetes namespace...")

        self.log.info(
            f"Enter the namespace to use for the Anyscale operator (default: {final_namespace}):"
        )
        final_namespace = click.prompt("", default=final_namespace, show_default=True)

        # Validate namespace (Kubernetes DNS-1123 label requirements)
        # Must be lowercase alphanumeric or hyphens, start and end with alphanumeric, max 63 chars

        if not final_namespace:
            raise click.ClickException("Namespace cannot be empty")
        if len(final_namespace) > 63:
            raise click.ClickException("Namespace must be 63 characters or less")
        if not re.match(r"^[a-z0-9]([-a-z0-9]*[a-z0-9])?$", final_namespace):
            raise click.ClickException(
                "Namespace must consist of lowercase alphanumeric characters or hyphens, "
                "and must start and end with an alphanumeric character"
            )

        self.log.info(f"Using namespace: {final_namespace}")

        return final_namespace

    def _generate_helm_values_file(  # noqa: PLR0913
        self,
        provider: str,
        cloud_deployment_id: str,
        region: str,
        namespace: str,
        infrastructure: InfrastructureResources,
        custom_path: Optional[str] = None,
        additional_values: Optional[Dict[str, str]] = None,
    ) -> str:
        """Generate Helm values file and save it locally."""
        self.log.info("Generating Helm values file...")

        # Create values dictionary starting with base values
        values: Dict[str, Any] = {
            "cloudProvider": provider,
            "cloudDeploymentId": cloud_deployment_id,
            "region": region,
            "operatorIamIdentity": infrastructure.iam_role_arn,
            "ingress-nginx": {"enabled": True},
        }

        if additional_values:
            for key, value in additional_values.items():
                if key not in values:
                    values[key] = value

        # Add control plane URL from ANYSCALE_HOST environment variable
        if ANYSCALE_HOST:
            values["controlPlaneURL"] = ANYSCALE_HOST
            self._debug(f"Using control plane URL: {ANYSCALE_HOST}")

        if custom_path:
            values_file_path = custom_path
        else:
            # Create filename with timestamp
            import datetime

            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"anyscale-helm-values-{provider}-{namespace}-{timestamp}.yaml"
            values_file_path = os.path.join(os.getcwd(), filename)

        with open(values_file_path, "w") as f:
            yaml.dump(values, f, default_flow_style=False, sort_keys=False)

        self.log.info(f"Generated Helm values file: {values_file_path}")

        return values_file_path

    def _execute_helm_command(self, helm_command: str) -> None:
        """Execute the helm command."""
        # Convert multi-line command to single line and execute
        single_line_command = helm_command.replace(" \\\n", " ").replace("\n", " ")

        self.log.info(f"Executing: {single_line_command}")

        try:
            subprocess.run(
                single_line_command,
                shell=True,
                check=True,
                capture_output=True,
                text=True,
            )
            self.log.info("Helm installation completed successfully")
        except subprocess.CalledProcessError as e:
            self.log.error(f"Helm installation failed: {e.stderr}")
            raise click.ClickException(
                f"Failed to install Anyscale operator: {e.stderr}"
            )

    def _verify_installation(
        self, cloud_id: str, namespace: str, cluster_info: ClusterInfo
    ) -> None:
        """Verify the Kubernetes installation."""
        self.log.info("Verifying installation...")

        # Get the cloud deployment
        cloud_resources = self.cloud_controller.get_cloud_resources(cloud_id)

        if not cloud_resources:
            raise click.ClickException("No cloud resources found for verification")

        cloud_deployment = cloud_resources[0]

        # Use the existing Kubernetes verifier
        verifier = KubernetesCloudDeploymentVerifier(
            self.log, self.cloud_controller.api_client
        )

        # Set up kubectl config for verification using the discovered context
        verifier.k8s_config = KubernetesConfig(
            context=cluster_info.context,  # Use the discovered context to avoid re-prompting
            operator_namespace=namespace,
        )

        # Sleep to avoid race condition where operator has not loaded its IAM identity
        import time

        time.sleep(5)

        # Run verification
        success = verifier.verify(cloud_deployment)

        if success:
            self.log.info("Verification completed successfully")
        else:
            self.log.error("Verification failed - please check the logs above")
            raise click.ClickException("Installation verification failed")


def setup_kubernetes_cloud(  # noqa: PLR0913
    provider: str,
    region: str,
    name: str,
    cluster_name: str,
    namespace: str = "anyscale-operator",
    project_id: Optional[str] = None,
    functional_verify: bool = False,
    yes: bool = False,
    values_file: Optional[str] = None,
    debug: bool = False,
) -> None:
    """
    Set up Anyscale on a Kubernetes cluster.

    This function can be called from multiple CLI commands and provides
    the core K8s setup functionality.

    Args:
        provider: Cloud provider (aws, gcp)
        region: Cloud region
        name: Name for the Anyscale cloud
        cluster_name: Kubernetes cluster name
        namespace: Namespace for Anyscale operator (default: anyscale-operator)
        project_id: GCP project ID (optional, for future GCP support)
        functional_verify: Whether to run functional verification
        yes: Skip confirmation prompts
        values_file: Optional path for Helm values file
        debug: Enable debug logging
    """
    cmd = KubernetesCloudSetupCommand(debug=debug)

    try:
        cmd.run(
            provider=provider,
            region=region,
            name=name,
            cluster_name=cluster_name,
            namespace=namespace,
            project_id=project_id,
            functional_verify=functional_verify,
            yes=yes,
            values_file=values_file,
        )
    except Exception as e:  # noqa: BLE001
        click.echo(f"Setup failed: {e}", err=True)
        raise click.Abort()
