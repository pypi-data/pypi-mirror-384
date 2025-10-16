# -*- coding: utf-8 -*-

"""
AWS ECS (Elastic Container Service) client wrapper.

This module provides a high-level interface for interacting with AWS ECS,
including service management, task operations, and container orchestration.
"""

from typing import Any, Dict, List

from core_aws.services.base import AwsClient, AwsClientException


class EcsClient(AwsClient):
    """
    Client for AWS ECS (Elastic Container Service).

    This client provides methods for managing ECS services, tasks, and container
    instances. Supports service updates, task listing, and service description
    operations with automatic error handling.

    Example:
        .. code-block:: python

            # Initialize client
            ecs = EcsClient(region="us-east-1")

            # List services in a cluster
            services = ecs.list_services(cluster="my-cluster")
            print(f"Services: {services['serviceArns']}")

            # Describe services
            details = ecs.describe_services(
                cluster="my-cluster",
                services=["my-service"]
            )

            # Update service desired count
            ecs.update_service(
                service="my-service",
                cluster="my-cluster",
                desiredCount=3
            )

            # List running tasks
            tasks = ecs.list_tasks(
                cluster="my-cluster",
                serviceName="my-service"
            )
        ..
    """

    client: "mypy_boto3_ecs.client.ECSClient"  # type: ignore[name-defined]

    def __init__(self, region: str, **kwargs: Any) -> None:
        """
        Initialize the ECS client.

        :param region: AWS region name (e.g., 'us-east-1', 'eu-west-1').
        :param kwargs: Additional arguments passed to boto3.client().
        """

        super().__init__("ecs", region_name=region, **kwargs)

    def list_services(
        self,
        cluster: str,
        **kwargs: Any
    ) -> Dict[str, Any]:
        """
        List services in an ECS cluster. Returns a list of service ARNs in
        the specified cluster. Results can be filtered by launch type and scheduling
        strategy. Supports pagination for clusters with many services.

        Reference:
            https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ecs/client/list_services.html

        :param cluster:
            Short name or full ARN of the cluster. If not specified, uses the
            default cluster.

        :param kwargs:
            Additional boto3 parameters:

            - **nextToken** (str):
                Token for pagination. Use the value from a previous response to
                get the next page of results.

            - **maxResults** (int):
                Maximum number of results per page (1-100). Default: 10.

            - **launchType** (str):
                Filter by launch type: 'EC2', 'FARGATE', or 'EXTERNAL'.

            - **schedulingStrategy** (str):
                Filter by scheduling strategy: 'REPLICA' or 'DAEMON'.

        :return:
            Dictionary containing service ARNs and pagination info:

            .. code-block:: python

                {
                    "serviceArns": [
                        "arn:aws:ecs:us-west-2:123456789012:service/my-cluster/my-service"
                    ],
                    "nextToken": "string",  # Present if more results available
                    "ResponseMetadata": {...}
                }
            ..

        :raises AwsClientException: If the operation fails.

        Example:
            .. code-block:: python

                ecs = EcsClient(region="us-east-1")

                # List all services in cluster
                services = ecs.list_services(cluster="my-cluster")
                print(f"Found {len(services['serviceArns'])} services")

                # List Fargate services with pagination
                services = ecs.list_services(
                    cluster="my-cluster",
                    launchType="FARGATE",
                    maxResults=50
                )

                # Handle pagination
                all_service_arns = []
                response = ecs.list_services(cluster="my-cluster")
                all_service_arns.extend(response["serviceArns"])

                while "nextToken" in response:
                    response = ecs.list_services(
                        cluster="my-cluster",
                        nextToken=response["nextToken"]
                    )
                    all_service_arns.extend(response["serviceArns"])
            ..
        """

        try:
            return self.client.list_services(
                cluster=cluster,
                **kwargs)

        except Exception as error:
            raise AwsClientException(error) from error

    def describe_services(
        self,
        cluster: str,
        services: List[str],
        **kwargs: Any
    ) -> Dict[str, Any]:
        """
        Retrieve detailed information about ECS services. Returns comprehensive
        information about specified services including configuration, deployment
        status, task definition, load balancers, service registries, and
        more. Up to 10 services can be described in a single operation.

        Reference:
            https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ecs/client/describe_services.html

        :param cluster:
            Short name or full ARN of the cluster hosting the services.
            Required if services are in non-default cluster.

        :param services:
            List of service names or ARNs to describe (max 10 per request).
            Example: ["my-service", "another-service"]

        :param kwargs:
            Additional boto3 parameters:

            - **include** (list):
                Additional information to include in response.
                Options: ['TAGS'] to include resource tags.

        :return:
            Dictionary containing service details:

            .. code-block:: python

                {
                    "services": [
                        {
                            "serviceName": "my-service",
                            "serviceArn": "arn:aws:ecs:...",
                            "clusterArn": "arn:aws:ecs:...",
                            "status": "ACTIVE",
                            "desiredCount": 2,
                            "runningCount": 2,
                            "pendingCount": 0,
                            "launchType": "FARGATE",
                            "taskDefinition": "arn:aws:ecs:...",
                            "deployments": [...],
                            "events": [...],
                            "loadBalancers": [...],
                            "networkConfiguration": {...},
                            "tags": [...]  # If include=['TAGS']
                        }
                    ],
                    "failures": [
                        {
                            "arn": "arn:aws:ecs:...",
                            "reason": "MISSING"
                        }
                    ]
                }
            ..

        :raises AwsClientException: If the operation fails.

        Example:
            .. code-block:: python

                ecs = EcsClient(region="us-east-1")

                # Describe single service
                details = ecs.describe_services(
                    cluster="my-cluster",
                    services=["my-service"]
                )

                service = details["services"][0]
                print(f"Service: {service['serviceName']}")
                print(f"Running: {service['runningCount']}/{service['desiredCount']}")
                print(f"Status: {service['status']}")

                # Describe multiple services with tags
                details = ecs.describe_services(
                    cluster="my-cluster",
                    services=["service-1", "service-2", "service-3"],
                    include=["TAGS"]
                )

                for service in details["services"]:
                    print(f"{service['serviceName']}: {service['taskDefinition']}")
                    for tag in service.get("tags", []):
                        print(f"  {tag['key']}: {tag['value']}")

                # Check for failures
                if details["failures"]:
                    for failure in details["failures"]:
                        print(f"Failed: {failure['arn']} - {failure['reason']}")
            ..
        """

        try:
            return self.client.describe_services(
                cluster=cluster,
                services=services,
                **kwargs)

        except Exception as error:
            raise AwsClientException(error) from error

    def update_service(
        self,
        service: str,
        **kwargs: Any
    ) -> Dict[str, Any]:
        """
        Update an ECS service configuration. Modifies service
        parameters including desired count, task definition, deployment
        configuration, network configuration, and task placement
        strategies. For services using rolling update (ECS)
        deployment controller.

        Reference:
            https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ecs/client/update_service.html

        :param service: Name or full ARN of the service to update.

        :param kwargs:
            Additional boto3 parameters (commonly used):

            - **cluster** (str):
                Cluster name or ARN. Default: default cluster.

            - **desiredCount** (int):
                Number of task instantiations to place and keep running.

            - **taskDefinition** (str):
                Task definition family and revision (family:revision) or full ARN.

            - **deploymentConfiguration** (dict):
                Deployment parameters:
                  - minimumHealthyPercent (int): Lower limit (0-100)
                  - maximumPercent (int): Upper limit (100-200)
                  - deploymentCircuitBreaker (dict): Circuit breaker config

            - **networkConfiguration** (dict):
                Network configuration for FARGATE launch type.

            - **platformVersion** (str):
                Platform version for Fargate tasks (e.g., "LATEST", "1.4.0").

            - **forceNewDeployment** (bool):
                Force new deployment even if no changes.

            - **healthCheckGracePeriodSeconds** (int):
                Grace period for load balancer health checks (0-2147483647).

            - **enableExecuteCommand** (bool):
                Enable ECS Exec for debugging.

            - **capacityProviderStrategy** (list):
                Capacity provider strategy to use.

            - **placementConstraints** (list):
                Task placement constraints.

            - **placementStrategy** (list):
                Task placement strategies.

        :return:
            Dictionary containing updated service information:

            .. code-block:: python

                {
                    "service": {
                        "serviceName": "my-service",
                        "serviceArn": "arn:aws:ecs:...",
                        "taskDefinition": "arn:aws:ecs:...",
                        "desiredCount": 3,
                        "runningCount": 2,
                        "pendingCount": 1,
                        "deployments": [
                            {
                                "status": "PRIMARY",
                                "taskDefinition": "arn:aws:ecs:...",
                                "desiredCount": 3,
                                "runningCount": 2
                            }
                        ],
                        "events": [...]
                    }
                }
            ..

        :raises AwsClientException: If the operation fails.

        Example:
            .. code-block:: python

                ecs = EcsClient(region="us-east-1")

                # Update desired count
                result = ecs.update_service(
                    service="my-service",
                    cluster="my-cluster",
                    desiredCount=5
                )
                print(f"Updated to {result['service']['desiredCount']} tasks")

                # Update task definition
                ecs.update_service(
                    service="my-service",
                    cluster="my-cluster",
                    taskDefinition="my-task:2"
                )

                # Force new deployment with deployment configuration
                ecs.update_service(
                    service="my-service",
                    cluster="my-cluster",
                    forceNewDeployment=True,
                    deploymentConfiguration={
                        "minimumHealthyPercent": 50,
                        "maximumPercent": 200,
                        "deploymentCircuitBreaker": {
                            "enable": True,
                            "rollback": True
                        }
                    }
                )

                # Enable ECS Exec for debugging
                ecs.update_service(
                    service="my-service",
                    cluster="my-cluster",
                    enableExecuteCommand=True
                )
            ..
        """

        try:
            return self.client.update_service(service=service, **kwargs)

        except Exception as error:
            raise AwsClientException(error) from error

    def list_tasks(self, **kwargs: Any) -> Dict[str, Any]:
        """
        List tasks in an ECS cluster. Returns a list of task ARNs. Filter
        by cluster, task definition family, container instance, launch type,
        starter principal, or desired status. Recently stopped tasks
        appear in results for at least one hour.

        Reference:
            https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ecs/client/list_tasks.html

        :param kwargs:
            Boto3 parameters for filtering:

            - **cluster** (str):
                Cluster name or ARN. Default: default cluster.

            - **containerInstance** (str):
                Container instance ID or ARN to filter by.

            - **family** (str):
                Task definition family name to filter by.

            - **serviceName** (str):
                Service name to filter tasks belonging to that service.

            - **desiredStatus** (str):
                Filter by task status: 'RUNNING' (default) or 'STOPPED'.
                Use 'STOPPED' for debugging failed/finished tasks.

            - **launchType** (str):
                Filter by launch type: 'EC2', 'FARGATE', or 'EXTERNAL'.

            - **startedBy** (str):
                Filter by principal that started the task.

            - **nextToken** (str):
                Pagination token from previous response.

            - **maxResults** (int):
                Maximum results per page (1-100). Default: 100.

        :return:
            Dictionary containing task ARNs and pagination info:

            .. code-block:: python

                {
                    "taskArns": [
                        "arn:aws:ecs:us-west-2:123456789012:task/my-cluster/abc123",
                        "arn:aws:ecs:us-west-2:123456789012:task/my-cluster/def456"
                    ],
                    "nextToken": "string",  # Present if more results available
                    "ResponseMetadata": {...}
                }
            ..

        :raises AwsClientException: If the operation fails.

        Example:
            .. code-block:: python

                ecs = EcsClient(region="us-east-1")

                # List all running tasks in cluster
                tasks = ecs.list_tasks(cluster="my-cluster")
                print(f"Running tasks: {len(tasks['taskArns'])}")

                # List tasks for specific service
                service_tasks = ecs.list_tasks(
                    cluster="my-cluster",
                    serviceName="my-service"
                )

                # List stopped tasks (for debugging)
                stopped_tasks = ecs.list_tasks(
                    cluster="my-cluster",
                    desiredStatus="STOPPED",
                    maxResults=50
                )

                # List tasks by task definition family
                family_tasks = ecs.list_tasks(
                    cluster="my-cluster",
                    family="my-task-family"
                )

                # List Fargate tasks started by specific principal
                fargate_tasks = ecs.list_tasks(
                    cluster="my-cluster",
                    launchType="FARGATE",
                    startedBy="arn:aws:iam::123456789012:user/admin"
                )

                # Handle pagination
                all_task_arns = []
                response = ecs.list_tasks(cluster="my-cluster")
                all_task_arns.extend(response["taskArns"])

                while "nextToken" in response:
                    response = ecs.list_tasks(
                        cluster="my-cluster",
                        nextToken=response["nextToken"]
                    )
                    all_task_arns.extend(response["taskArns"])

                print(f"Total tasks: {len(all_task_arns)}")
            ..
        """

        try:
            return self.client.list_tasks(**kwargs)

        except Exception as error:
            raise AwsClientException(error) from error
