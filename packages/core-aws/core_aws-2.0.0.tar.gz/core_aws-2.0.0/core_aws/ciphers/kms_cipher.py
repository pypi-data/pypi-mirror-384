# -*- coding: utf-8 -*-

from __future__ import annotations

from typing import Optional

from aws_encryption_sdk import CommitmentPolicy  # type: ignore[import-untyped]
from aws_encryption_sdk import EncryptionSDKClient  # type: ignore[import-untyped]
from aws_encryption_sdk import StrictAwsKmsMasterKeyProvider  # type: ignore[import-untyped]
from botocore.session import Session
from core_ciphers.base import ICipher


class KMSCipher(ICipher):
    """ It uses the AWS Encryption SDK for Python """

    def __init__(
        self,
        key_arn: str,
        botocore_session: Optional[Session] = None,
        **kwargs
    ) -> None:
        super().__init__(**kwargs)

        if not key_arn or not isinstance(key_arn, str):
            raise ValueError("key_arn must be a non-empty string")

        if not key_arn.startswith("arn:aws:kms:"):
            raise ValueError(
                "key_arn must be a valid AWS KMS ARN starting "
                "with 'arn:aws:kms:'"
            )

        self.session = botocore_session
        self.key_arn = key_arn

        self.client = EncryptionSDKClient(
            commitment_policy=CommitmentPolicy.REQUIRE_ENCRYPT_REQUIRE_DECRYPT)

        kms_kwargs = {"key_ids": [self.key_arn]}
        if self.session:
            kms_kwargs["botocore_session"] = self.session  # type: ignore

        self.master_key_provider = StrictAwsKmsMasterKeyProvider(**kms_kwargs)

    def encrypt(self, data: bytes, *args, **kwargs) -> bytes:
        if not isinstance(data, bytes):
            raise TypeError("data must be bytes")

        ciphertext, _ = self.client.encrypt(
            source=data,
            key_provider=self.master_key_provider)

        return ciphertext

    def decrypt(self, data: bytes, *args, **kwargs) -> str:
        if not isinstance(data, bytes):
            raise TypeError("data must be bytes")

        plaintext, _ = self.client.decrypt(
            source=data,
            key_provider=self.master_key_provider)

        return plaintext.decode(encoding=self.encoding)
