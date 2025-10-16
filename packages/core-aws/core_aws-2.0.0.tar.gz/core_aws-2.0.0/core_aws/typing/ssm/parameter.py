# -*- coding: utf-8 -*-

"""
Type definitions for AWS Systems Manager (SSM) Parameter Store.

This module provides TypedDict definitions for SSM parameter structures
returned by boto3 SSM client operations.
"""

from datetime import datetime
from typing import Literal, TypedDict


class SSMParameter(TypedDict, total=False):
    """
    Type definition for an AWS SSM Parameter.

    Represents the structure of a parameter object returned by AWS Systems Manager
    Parameter Store operations such as get_parameter() and get_parameters_by_path().

    Reference:
        https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ssm/client/get_parameter.html

    Example:
        .. code-block:: python

            parameter: SSMParameter = {
                "Name": "/myapp/prod/database_url",
                "Type": "SecureString",
                "Value": "postgresql://...",
                "Version": 1,
                "LastModifiedDate": datetime(2024, 1, 1),
                "ARN": "arn:aws:ssm:us-east-1:123456789012:parameter/myapp/prod/database_url"
            }
        ..
    """

    Name: str
    """The name/path of the parameter (e.g., '/myapp/prod/database_url')."""

    Type: Literal["String", "StringList", "SecureString"]
    """The parameter type: String, StringList, or SecureString."""

    Value: str
    """The parameter value. Decrypted if the parameter is a SecureString."""

    Version: int
    """The version number of the parameter."""

    LastModifiedDate: datetime
    """The date and time the parameter was last modified."""

    ARN: str
    """The Amazon Resource Name (ARN) of the parameter."""

    Selector: str
    """
    The parameter version or label used in the request (optional).
    Either a version number or a label like ':latest'.
    """

    SourceResult: str
    """The raw result or response from the source (optional)."""

    DataType: str
    """
    The data type of the parameter (optional).
    Values: 'text' (default), 'aws:ec2:image'.
    """
