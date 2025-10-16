# -*- coding: utf-8 -*-

"""
AWS service client wrappers.

This module provides high-level client wrappers for AWS services with improved
error handling, type safety, and convenience methods. Each service client
inherits from the base AwsClient class.

Available Services:
    - CloudFormation: Infrastructure as Code service client
    - DynamoDB: NoSQL database service client
    - ECS: Elastic Container Service client
    - Kinesis: Data streaming service client
    - Lambda: Serverless compute decorators and utilities
    - S3: Object storage service client
    - SNS: Simple Notification Service client
    - SQS: Simple Queue Service client
    - SSM: Systems Manager (Parameter Store, Secrets Manager) client

Base Classes:
    - AwsClient: Base class for all AWS service clients
    - AwsClientException: Custom exception for AWS client operations

Example:
    .. code-block:: python

        from core_aws.services import (
            AwsClient,
            DynamoDbClient,
            S3Client,
            SnsClient,
            SqsClient,
        )

        # Initialize clients
        sqs = SqsClient(region_name="us-east-1")
        sns = SnsClient(region_name="us-east-1")
        s3 = S3Client(region_name="us-east-1")
        dynamo = DynamoDbClient(region_name="us-east-1")

        # Use service clients
        sqs.send_message(queue_url="https://...", message_body="Hello")
        sns.publish(topic_arn="arn:aws:sns:...", message="World")
        s3.put_object(bucket="my-bucket", key="file.txt", body=b"data")

        # Query DynamoDB
        dynamo.query(
            table_name="MyTable",
            key_condition_expression="id = :id",
            expression_attribute_values={":id": {"S": "123"}}
        )
    ..
"""

from __future__ import annotations

from core_aws.services.base import AwsClient
from core_aws.services.base import AwsClientException
from core_aws.services.cloud_formation.client import CloudFormationClient
from core_aws.services.dynamo.client import DynamoDbClient
from core_aws.services.ecs.client import EcsClient
from core_aws.services.kinesis.client import KinesisClient
from core_aws.services.s3.client import S3Client
from core_aws.services.sns.client import SnsClient
from core_aws.services.sns.client import SnsMessage
from core_aws.services.sqs.client import SqsClient
from core_aws.services.ssm.client import SsmClient

__all__ = [
    # Base classes...
    "AwsClient",
    "AwsClientException",
    # Service clients...
    "CloudFormationClient",
    "DynamoDbClient",
    "EcsClient",
    "KinesisClient",
    "S3Client",
    "SnsClient",
    "SnsMessage",
    "SqsClient",
    "SsmClient",
]
