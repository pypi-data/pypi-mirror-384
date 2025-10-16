# -*- coding: utf-8 -*-

from dataclasses import dataclass


@dataclass(frozen=True)
class CognitoIdentity:
    """
    Information related to the AWS Cognito identity that
    authorize the request.
    """

    cognito_identity_id: str
    """The authenticated Amazon Cognito identity."""

    cognito_identity_pool_id: str
    """The Amazon Cognito identity pool that authorized the invocation."""
