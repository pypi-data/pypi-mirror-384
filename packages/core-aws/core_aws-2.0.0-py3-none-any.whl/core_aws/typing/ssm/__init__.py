# -*- coding: utf-8 -*-

"""
AWS Systems Manager (SSM) type definitions.

This module provides type definitions for AWS Systems Manager Parameter Store
structures used in boto3 SSM client operations.
"""

from .parameter import SSMParameter


__all__ = [
    "SSMParameter",
]
