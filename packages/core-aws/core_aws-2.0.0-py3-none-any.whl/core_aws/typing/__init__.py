# -*- coding: utf-8 -*-

"""
AWS type definitions for Lambda and related services.

This module provides comprehensive type definitions for:
- AWS Lambda contexts and events
- AWS Cognito identity
- Mobile client contexts
- AWS Systems Manager (SSM) Parameter Store
"""

from .cognito import CognitoIdentity

from .lambdas import (
    ClientContext,
    KinesisData,
    KinesisEvent,
    KinesisRecord,
    LambdaContext,
    SNSEvent,
    SNSMessage,
    SNSRecord,
    SQSEvent,
    SQSMessageAttributes,
    SQSRecord,
)

from .mobile import MobileClient
from .ssm import SSMParameter


__all__ = [
    # Cognito types...
    "CognitoIdentity",
    # Mobile types...
    "MobileClient",
    # Lambda context types...
    "ClientContext",
    "LambdaContext",
    # Lambda Event types - SQS...
    "SQSEvent",
    "SQSRecord",
    "SQSMessageAttributes",
    # Lambda Event types - SNS...
    "SNSEvent",
    "SNSRecord",
    "SNSMessage",
    # Lambda Event types - Kinesis...
    "KinesisEvent",
    "KinesisRecord",
    "KinesisData",
    # SSM types...
    "SSMParameter",
]
