# -*- coding: utf-8 -*-

"""
AWS CloudFormation client wrapper.

This module provides a high-level interface for interacting with AWS CloudFormation,
including stack description and output value retrieval operations.
"""

from typing import Any, Dict, Optional

from core_aws.services.base import AwsClient
from core_aws.services.base import AwsClientException


class CloudFormationClient(AwsClient):
    """
    Client for AWS CloudFormation.

    This client provides methods for interacting with CloudFormation stacks,
    including retrieving stack information and extracting output values.
    Simplifies common stack inspection operations with automatic error handling.

    Example:
        .. code-block:: python

            # Initialize client
            cfn = CloudFormationClient(region="us-east-1")

            # Get stack details
            stack = cfn.describe_stack(stack_name="my-app-stack")
            print(f"Stack Status: {stack['StackStatus']}")
            print(f"Stack Outputs: {stack['Outputs']}")

            # Get specific output value by export name
            vpc_id = cfn.get_output_value(
                stack_name="my-app-stack",
                export_name="MyAppVpcId"
            )
            if vpc_id:
                print(f"VPC ID: {vpc_id}")
        ..
    """

    client: "mypy_boto3_cloudformation.client.CloudFormationClient"  # type: ignore[name-defined]

    def __init__(self, region: str, **kwargs: Any) -> None:
        """
        Initialize the CloudFormation client.

        :param region: AWS region name (e.g., 'us-east-1', 'eu-west-1').
        :param kwargs: Additional arguments passed to boto3.client().
        """
        super().__init__("cloudformation", region_name=region, **kwargs)

    def describe_stack(self, stack_name: str) -> Dict[str, Any]:
        """
        Retrieve detailed information about a CloudFormation
        stack. Returns comprehensive stack details including status,
        parameters, outputs, tags, and capabilities. This is a
        convenience wrapper around `describe_stacks` that returns
        only the first stack.

        Reference:
            https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/cloudformation/client/describe_stacks.html

        :param stack_name:
            Name or ARN of the CloudFormation stack.
            Example: "my-app-stack" or full ARN.

        :return:
            Dictionary containing stack details:

            .. code-block:: python

                {
                    "StackId": "arn:aws:cloudformation:...",
                    "StackName": "my-app-stack",
                    "Description": "My application infrastructure",
                    "Parameters": [
                        {
                            "ParameterKey": "InstanceType",
                            "ParameterValue": "t3.micro"
                        }
                    ],
                    "CreationTime": datetime(2024, 1, 1, 0, 0, 0),
                    "LastUpdatedTime": datetime(2024, 6, 1, 0, 0, 0),
                    "StackStatus": "CREATE_COMPLETE",  # or UPDATE_COMPLETE, etc.
                    "StackStatusReason": "string",
                    "Outputs": [
                        {
                            "OutputKey": "VpcId",
                            "OutputValue": "vpc-12345678",
                            "Description": "VPC ID",
                            "ExportName": "MyAppVpcId"
                        }
                    ],
                    "Tags": [
                        {
                            "Key": "Environment",
                            "Value": "production"
                        }
                    ],
                    "Capabilities": ["CAPABILITY_IAM"],
                    "DriftInformation": {
                        "StackDriftStatus": "IN_SYNC" | "DRIFTED" | "NOT_CHECKED"
                    }
                }
            ..

        :raises AwsClientException: If stack doesn't exist or operation fails.

        Example:
            .. code-block:: python

                cfn = CloudFormationClient(region="us-east-1")

                # Get stack details
                stack = cfn.describe_stack(stack_name="my-app-stack")

                print(f"Stack: {stack['StackName']}")
                print(f"Status: {stack['StackStatus']}")
                print(f"Created: {stack['CreationTime']}")

                # Check stack parameters
                for param in stack.get("Parameters", []):
                    print(f"  {param['ParameterKey']}: {param['ParameterValue']}")

                # Check stack outputs
                for output in stack.get("Outputs", []):
                    print(f"  {output['OutputKey']}: {output['OutputValue']}")

                # Check stack status before operations
                if stack["StackStatus"] in ["CREATE_COMPLETE", "UPDATE_COMPLETE"]:
                    print("Stack is stable")
                elif "IN_PROGRESS" in stack["StackStatus"]:
                    print("Stack operation in progress")
                elif "FAILED" in stack["StackStatus"]:
                    print(f"Stack failed: {stack.get('StackStatusReason', 'Unknown')}")
            ..
        """

        try:
            return self.client.describe_stacks(StackName=stack_name)["Stacks"][0]

        except Exception as error:
            raise AwsClientException(error) from error

    def get_output_value(
        self,
        stack_name: str,
        export_name: str,
    ) -> Optional[str]:
        """
        Retrieve a specific output value from a CloudFormation stack by export name.

        Searches through stack outputs to find the value associated with the
        specified export name. Returns None if the export name is not found.
        This is useful for retrieving exported resource identifiers (VPC IDs,
        security group IDs, etc.) from stacks.

        :param stack_name:
            Name or ARN of the CloudFormation stack.

        :param export_name:
            Export name of the output value to retrieve. This is the
            "ExportName" field in the stack outputs, not the "OutputKey".

        :return:
            Output value as string if found, None if export name doesn't exist.

        :raises AwsClientException: If stack doesn't exist or operation fails.

        Example:
            .. code-block:: python

                cfn = CloudFormationClient(region="us-east-1")

                # Get specific output by export name
                vpc_id = cfn.get_output_value(
                    stack_name="network-stack",
                    export_name="MyAppVpcId"
                )

                if vpc_id:
                    print(f"VPC ID: {vpc_id}")
                else:
                    print("Export 'MyAppVpcId' not found in stack outputs")

                # Get multiple outputs
                exports_to_fetch = [
                    "MyAppVpcId",
                    "MyAppSubnetId",
                    "MyAppSecurityGroupId"
                ]

                for export in exports_to_fetch:
                    value = cfn.get_output_value("network-stack", export)
                    if value:
                        print(f"{export}: {value}")
                    else:
                        print(f"{export}: Not found")

                # Use output value in another operation
                db_endpoint = cfn.get_output_value(
                    stack_name="database-stack",
                    export_name="DatabaseEndpoint"
                )
                if db_endpoint:
                    # Use the endpoint in your application
                    connection_string = f"postgresql://{db_endpoint}:5432/mydb"
            ..

        Note:
            - Export names must be unique within a region
            - This method searches by ExportName, not OutputKey
            - Returns None (not an error) if export name is not found
            - Automatically handles stacks without Outputs section
        """

        try:
            stack = self.describe_stack(stack_name)

            for output in stack.get("Outputs", []):
                if output.get("ExportName") == export_name:
                    return output["OutputValue"]

            return None

        except Exception as error:
            raise AwsClientException(error) from error
