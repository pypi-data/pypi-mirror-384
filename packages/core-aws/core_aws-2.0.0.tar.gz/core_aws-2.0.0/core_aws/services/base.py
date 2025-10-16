# -*- coding: utf-8 -*-

"""
Base classes for AWS service clients.

This module provides the foundational classes for all AWS service client
wrappers in the core-aws library.
"""

from typing import Any

import boto3
import botocore.client


class AwsClient:
    """
    Base class for all AWS service client wrappers.

    This class provides a common interface for creating boto3 clients with
    consistent error handling and initialization patterns. All service-specific
    client classes should inherit from this base class.

    :param client: The underlying boto3 client instance for the AWS service.

    Example:
        .. code-block:: python

            class MyServiceClient(AwsClient):
                def __init__(self, region: str = "us-east-1", **kwargs):
                    super().__init__(
                        service="my_service",
                        region_name=region,
                        **kwargs
                    )

                def my_operation(self):
                    return self.client.some_operation()
        ..
    """

    client: botocore.client.BaseClient

    def __init__(self, service: str, **kwargs: Any) -> None:
        """
        Initialize an AWS service client. Creates a boto3 client
        for the specified AWS service with the provided
        configuration options.

        :param service: AWS service name (e.g., 's3', 'sqs', 'ssm', 'lambda').

        :param kwargs:
            Additional arguments passed to boto3.client():
              - region_name: AWS region (e.g., 'us-east-1').
              - aws_access_key_id: AWS access key ID.
              - aws_secret_access_key: AWS secret access key.
              - aws_session_token: AWS session token.
              - endpoint_url: Custom endpoint URL (for LocalStack, etc.).
              - config: botocore.client.Config instance.
              - Any other boto3.client() parameters.

        :raises AwsClientException: If client creation fails.

        Example:
            .. code-block:: python

                # Standard usage
                client = AwsClient("s3", region_name="us-east-1")

                # With custom endpoint (LocalStack)
                client = AwsClient(
                    "sqs",
                    endpoint_url="http://localhost:4566",
                    region_name="us-east-1"
                )
            ..
        """

        try:
            self.client = boto3.client(service, **kwargs)  # type: ignore[call-overload]

        except Exception as error:
            raise AwsClientException(
                f"Failed to create boto3 client for service '{service}': {error}"
            ) from error


class AwsClientException(Exception):
    """
    Custom exception for AWS client operations. This exception is
    raised when AWS client operations fail. It can wrap the original
    exception or provide a custom error message.

    Usage:
        .. code-block:: python

            # Simple pass-through (preserves stack trace with 'from')
            try:
                client.some_operation()
            except Exception as error:
                raise AwsClientException(error) from error

            # With custom message
            try:
                client.some_operation()
            except Exception as error:
                raise AwsClientException(f"Failed to do X: {error}") from error

            # Custom message only (no original exception)
            raise AwsClientException("Operation failed: custom reason")
        ..
    """
