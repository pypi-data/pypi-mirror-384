# -*- coding: utf-8 -*-

"""
AWS S3 (Simple Storage Service) client wrapper.

This module provides a high-level interface for interacting with AWS S3,
including bucket operations, object upload/download, and batch operations.
"""

from io import BytesIO
from typing import Any
from typing import Dict
from typing import Iterator
from typing import List
from typing import Optional
from typing import Union

from botocore.client import Config
from botocore.exceptions import ClientError
from core_mixins import StrEnum

from core_aws.services.base import AwsClient
from core_aws.services.base import AwsClientException


class S3ACL(StrEnum):  # type: ignore[assignment]
    """
    Enum for S3 canned ACL (Access Control List) values.

    These are predefined access control lists that define common access
    patterns for S3 buckets and objects. AWS recommends using bucket
    policies and IAM policies instead of ACLs for most access control needs.

    Reference:
        https://docs.aws.amazon.com/AmazonS3/latest/userguide/acl-overview.html#canned-acl
    """

    PRIVATE = "private"
    """Owner gets FULL_CONTROL. No one else has access rights."""

    PUBLIC_READ = "public-read"
    """Owner gets FULL_CONTROL. AllUsers group gets READ access."""

    PUBLIC_READ_WRITE = "public-read-write"
    """Owner gets FULL_CONTROL. AllUsers group gets READ and WRITE access."""

    AUTHENTICATED_READ = "authenticated-read"
    """Owner gets FULL_CONTROL. AuthenticatedUsers group gets READ access."""


class S3ObjectOwnership(StrEnum):  # type: ignore[assignment]
    """
    Enum for S3 object ownership settings.

    Controls object ownership and whether ACLs are enabled for the bucket.
    This setting applies to all objects in the bucket.

    Reference:
        https://docs.aws.amazon.com/AmazonS3/latest/userguide/about-object-ownership.html
    """

    BUCKET_OWNER_ENFORCED = "BucketOwnerEnforced"
    """
    ACLs are disabled. Bucket owner automatically owns and has full control
    over all objects in the bucket. All access control must be done via
    bucket policies and IAM policies.
    """

    BUCKET_OWNER_PREFERRED = "BucketOwnerPreferred"
    """
    Bucket owner owns objects if they are uploaded with the
    bucket-owner-full-control canned ACL. Otherwise, object writer
    retains ownership.
    """

    OBJECT_WRITER = "ObjectWriter"
    """
    Object uploader retains ownership. The AWS account that uploads
    an object owns the object, has full control over it, and can
    grant other users access to it through ACLs.
    """


class S3Client(AwsClient):
    """
    Client for AWS S3 (Simple Storage Service).

    This client provides methods for managing S3 buckets and objects,
    including upload, download, copy, delete, and list operations.
    Supports both single-part and multipart operations with automatic
    pagination handling.

    Example:
        .. code-block:: python

            # Initialize client
            s3 = S3Client(region_name="us-east-1")

            # Check if bucket exists
            if s3.does_bucket_exist("my-bucket"):
                print("Bucket exists")

            # Upload a file
            s3.upload_file(
                bucket="my-bucket",
                key="data/file.csv",
                path="/local/path/file.csv"
            )

            # List all objects
            for obj in s3.list_all_objects("my-bucket", "data/"):
                print(f"{obj['Key']}: {obj['Size']} bytes")

            # Download a file
            s3.download_file(
                bucket="my-bucket",
                key="data/file.csv",
                local_path="/local/download/file.csv"
            )
        ..
    """

    client: "mypy_boto3_s3.client.S3Client"  # type: ignore[name-defined]

    def __init__(
        self,
        signature_version: str = "s3v4",
        **kwargs: Any
    ) -> None:
        """
        Initialize the S3 client.

        :param signature_version:
            S3 signature version. Default: "s3v4" (recommended).
            Options: "s3v4" (AWS Signature Version 4), "s3" (legacy).

        :param kwargs:
            Additional arguments passed to boto3.client():
              - region_name: AWS region (e.g., 'us-east-1')
              - endpoint_url: Custom endpoint (for LocalStack, MinIO, etc.)
              - aws_access_key_id, aws_secret_access_key, aws_session_token

        Example:
            .. code-block:: python

                # Standard S3
                s3 = S3Client(region_name="us-east-1")

                # With custom endpoint (LocalStack)
                s3_local = S3Client(
                    endpoint_url="http://localhost:4566",
                    region_name="us-east-1"
                )

                # Legacy signature version
                s3_legacy = S3Client(signature_version="s3")
            ..
        """

        super().__init__(
            service="s3",
            config=Config(
                signature_version=signature_version,
            ),
            **kwargs
        )

    def create_bucket(
        self,
        bucket: str,
        acl: Optional[Union[S3ACL, str]] = None,
        object_ownership: Optional[Union[S3ObjectOwnership, str]] = None,
        **kwargs: Any
    ) -> Dict[str, Any]:
        """
        Create a new S3 bucket in the specified region. Bucket names must be
        globally unique across all AWS accounts. For regions outside us-east-1,
        a LocationConstraint must be specified.

        Reference:
            https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/s3/client/create_bucket.html

        :param bucket:
            Name of the bucket to create. Must be:
            - 3-63 characters long
            - Lowercase letters, numbers, hyphens, and periods only
            - Must start and end with a letter or number
            - Must not be formatted as an IP address
            - Globally unique across all AWS accounts

        :param acl:
            Optional canned ACL to apply to the bucket. Options:

            - **private** (default): Owner gets FULL_CONTROL. No one else has access.
            - **public-read**: Owner gets FULL_CONTROL. AllUsers get READ access.
            - **public-read-write**: Owner gets FULL_CONTROL. AllUsers get READ and WRITE access.
            - **authenticated-read**: Owner gets FULL_CONTROL. AuthenticatedUsers get READ access.

            Note: AWS recommends using bucket policies instead of ACLs for access control.

        :param object_ownership:
            Optional object ownership setting. Controls object ownership and ACL behavior:

            - **BucketOwnerEnforced**: ACLs disabled, bucket owner owns all objects
            - **BucketOwnerPreferred**: Bucket owner owns objects if uploaded with bucket-owner-full-control ACL
            - **ObjectWriter**: Object uploader retains ownership (default legacy behavior)

        :param kwargs:
            Additional boto3 parameters:

            - **CreateBucketConfiguration** (dict): Bucket configuration with:
                - **LocationConstraint** (str): AWS region (e.g., 'us-west-2').
                  Required for all regions except us-east-1.

            - **GrantFullControl** (str): Grants READ, WRITE, READ_ACP, and WRITE_ACP permissions
            - **GrantRead** (str): Grants READ permission
            - **GrantReadACP** (str): Grants READ_ACP permission
            - **GrantWrite** (str): Grants WRITE permission
            - **GrantWriteACP** (str): Grants WRITE_ACP permission
            - **ObjectLockEnabledForBucket** (bool): Enable object lock (requires versioning)

        :return:
            Dictionary containing bucket creation response:

            .. code-block:: python

                {
                    "Location": "string"  # URI of the created bucket
                }
            ..

        :raises AwsClientException:
            If bucket creation fails (e.g., name already exists, invalid name, permission denied).

        Example:
            .. code-block:: python

                from core_aws.services.s3.client import S3Client, S3ACL, S3ObjectOwnership

                s3 = S3Client(region_name="us-east-1")

                # Create bucket in us-east-1 (default region)
                response = s3.create_bucket(bucket="my-unique-bucket-name")
                print(f"Created bucket at: {response['Location']}")

                # Create bucket in a specific region
                s3_west = S3Client(region_name="us-west-2")
                response = s3_west.create_bucket(
                    bucket="my-west-bucket",
                    CreateBucketConfiguration={
                        "LocationConstraint": "us-west-2"
                    }
                )

                # Create bucket with object ownership controls (using enum)
                response = s3.create_bucket(
                    bucket="my-controlled-bucket",
                    object_ownership=S3ObjectOwnership.BUCKET_OWNER_ENFORCED
                )

                # Create private bucket with explicit ACL (using enum)
                response = s3.create_bucket(
                    bucket="my-private-bucket",
                    acl=S3ACL.PRIVATE
                )

                # Create public-read bucket (string also works)
                response = s3.create_bucket(
                    bucket="my-public-bucket",
                    acl="public-read"
                )

                # Create bucket with object lock enabled
                response = s3.create_bucket(
                    bucket="my-locked-bucket",
                    ObjectLockEnabledForBucket=True
                )
            ..

        Note:
          - Bucket names must be globally unique across all AWS accounts
          - For regions other than us-east-1, must specify CreateBucketConfiguration
          - Bucket creation is eventually consistent
          - Maximum 100 buckets per AWS account by default
        """

        create_kwargs: Dict[str, Any] = {"Bucket": bucket}

        if acl:
            create_kwargs["ACL"] = acl

        if object_ownership:
            create_kwargs["ObjectOwnership"] = object_ownership

        # Add any additional kwargs
        create_kwargs.update(kwargs)

        try:
            return self.client.create_bucket(**create_kwargs)

        except ClientError as error:
            raise AwsClientException(error) from error

    def does_bucket_exist(self, bucket: str) -> bool:
        """
        Check if an S3 bucket exists and is accessible. Performs a lightweight
        list operation to verify bucket existence
        and access permissions.

        :param bucket: Name of the S3 bucket to check.

        :return: True if bucket exists and is accessible, False if bucket doesn't exist.

        :raises AwsClientException: If access is denied or other errors occur.

        Example:
            .. code-block:: python

                s3 = S3Client(region_name="us-east-1")

                if s3.does_bucket_exist("my-bucket"):
                    print("Bucket exists and is accessible")
                else:
                    print("Bucket does not exist")
            ..
        """

        try:
            self.client.list_objects_v2(Bucket=bucket, MaxKeys=1)
            return True

        except ClientError as error:
            if error.response.get("Error", {}).get("Code") == "NoSuchBucket":
                return False

            raise AwsClientException(error) from error

    def list_objects(
        self,
        bucket: str,
        prefix: str = "",
        **kwargs: Any
    ) -> Dict[str, Any]:
        """
        List objects in an S3 bucket (single page, up to 1000
        objects). Returns a single page of results. For listing all
        objects with automatic pagination, use `list_all_objects()`
        instead.

        Reference:
            https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/s3.html#S3.Client.list_objects

        :param bucket: Name of the S3 bucket.
        :param prefix: Object key prefix filter (e.g., "folder/subfolder/").
        :param kwargs: Additional boto3 parameters (Delimiter, MaxKeys, Marker, etc.).

        :return:
            Dictionary containing object listing with structure:

            .. code-block:: python

                {
                    "IsTruncated": True|False,
                    "Marker": "string",
                    "NextMarker": "string",
                    "Contents": [
                        {
                            "Key": "string",
                            "LastModified": datetime(2015, 1, 1),
                            "ETag": "string",
                            "ChecksumAlgorithm": [
                                "CRC32"|"CRC32C"|"SHA1"|"SHA256",
                            ],
                            "Size": 123,
                            "StorageClass": "STANDARD" | ... | "GLACIER" ",
                            "Owner": {
                                "DisplayName": "string",
                                "ID": "string"
                            },
                            "RestoreStatus": {
                                "IsRestoreInProgress": True|False,
                                "RestoreExpiryDate": datetime(2015, 1, 1)
                            }
                        },
                    ],
                    "Name": "string",
                    "Prefix": "string",
                    "Delimiter": "string",
                    "MaxKeys": 123,
                    "CommonPrefixes": [
                        {
                            "Prefix": "string"
                        },
                    ],
                    "EncodingType": "url",
                    "RequestCharged": "requester"
                }
            ..
        """

        try:
            return self.client.list_objects(Bucket=bucket, Prefix=prefix, **kwargs)

        except Exception as error:
            raise AwsClientException(error) from error

    def list_all_objects(
        self,
        bucket: str,
        prefix: str = "",
        **kwargs: Any
    ) -> Iterator[Dict[str, Any]]:
        """
        Retrieve information of all objects (files) into s3 bucket. This way you don"t need
        to worry about pagination...

        :param bucket: Bucket name.
        :param prefix: Objects prefix.
        :param kwargs:

        :return: An iterator that contains dictionaries with the following structure

            .. code-block:: python

                {
                    "Key": "string",
                    "LastModified": datetime(2015, 1, 1),
                    "ETag": "string",
                    "ChecksumAlgorithm": [
                        "CRC32"|"CRC32C"|"SHA1"|"SHA256",
                    ],
                    "Size": 123,
                    "StorageClass": "STANDARD" | ... | "GLACIER" ",
                    "Owner": {
                        "DisplayName": "string",
                        "ID": "string"
                    },
                    "RestoreStatus": {
                        "IsRestoreInProgress": True|False,
                        "RestoreExpiryDate": datetime(2015, 1, 1)
                    }
                }
            ..
        """

        new_kwargs = {"Bucket": bucket, "Prefix": prefix, **kwargs}
        is_truncated = True
        latest_key = None

        try:
            while is_truncated:
                res = self.client.list_objects(**new_kwargs)
                for record in res.get("Contents", []):
                    latest_key = record["Key"]
                    yield record

                is_truncated = res.get("IsTruncated", False)
                if is_truncated:
                    new_kwargs["Marker"] = latest_key

        except Exception as error:
            raise AwsClientException(error) from error

    def upload_file(
        self,
        bucket: str,
        key: str,
        path: str,
        **kwargs: Any
    ) -> None:
        """
        Upload a file to AWS bucket...
        https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/s3/client/upload_file.html

        :param bucket: The bucket name of the bucket containing the object.
        :param key: Key/path of the object.
        :param path: (str) -- The path to the file to upload.
        :param kwargs:

        :return:
        """

        try:
            return self.client.upload_file(
                Filename=path,
                Bucket=bucket, Key=key,
                **kwargs)

        except Exception as error:
            raise AwsClientException(error) from error

    def upload_object(
        self,
        bucket: str,
        key: str,
        data: BytesIO,
        **kwargs
    ) -> None:
        """
        Upload a file (in form StringIO) to AWS bucket...
        https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/s3.html#S3.Client.upload_fileobj

        :param bucket: The bucket name of the bucket containing the object.
        :param key: Key/path of the object.

        :param data:
            A file-like object to upload. At a minimum, it must implement the
            read method, and must return bytes.

        :param kwargs:
        """

        try:
            self.client.upload_fileobj(
                Fileobj=data,
                Bucket=bucket,
                Key=key,
                **kwargs
            )

        except Exception as error:
            raise AwsClientException(error) from error

    def download_file(
        self,
        bucket: str,
        key: str,
        local_path: str,
        **kwargs
    ) -> str:
        """
        Download file from the S3 bucket to the local path...
        https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/s3/client/download_file.html

        :param local_path: Path to save the file locally.
        :param bucket: The bucket name of the bucket containing the object.
        :param key: Key/path of the object.
        :param kwargs:

        :return: The local file where the file was stored.
        """

        try:
            self.client.download_file(Bucket=bucket, Key=key, Filename=local_path, **kwargs)
            return local_path

        except Exception as error:
            raise AwsClientException(error) from error

    def download_object(
        self,
        buffer: BytesIO,
        bucket: str,
        key: str,
        **kwargs
    ) -> None:
        """
        Download an object from S3 to a file-like object. The file-like object must
        be in binary mode...

        https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/s3/client/download_fileobj.html

        :param bucket: The bucket name of the bucket containing the object.
        :param key: Key/path of the object.

        :param buffer:
            (a file-like object) -- A file-like object to
            download into. At a minimum, it must implement
            the write method and must accept bytes.

        :param kwargs:
        """

        try:
            self.client.download_fileobj(
                Bucket=bucket,
                Key=key,
                Fileobj=buffer,
                **kwargs
            )

        except Exception as error:
            raise AwsClientException(error) from error

    def copy(
        self,
        copy_source: Dict,
        bucket: str,
        key: str,
        **kwargs
    ) -> None:
        """
        Copy an object from one S3 location to another. This is a managed transfer which will
        perform a multipart copy in multiple threads if necessary...

        https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/s3.html#S3.Bucket.copy

        :type copy_source: dict
        :param copy_source: The name of the source bucket, key name of the
            source object, and optional version ID of the source object. The
            dictionary format is:
            ``{"Bucket": "bucket", "Key": "key", "VersionId": "id"}``. Note
            that the ``VersionId`` key is optional and may be omitted.

        :type bucket: str
        :param bucket: The name of the bucket to copy to

        :type key: str
        :param key: The name of the key to copy to

        :param kwargs: Extra arguments.
            ExtraArgs: dict -- Extra arguments that may be passed to the client operation

            Callback: function
                A method which takes a number of bytes transferred to
                be periodically called during the copy.

            SourceClient: botocore or boto3 Client
                The client to be used for operation that
                may happen at the source object. For example, this client is
                used for the head_object that determines the size of the copy.
                If no client is provided, the current client is used as the client
                for the source object.

            ConfigLoader: boto3.s3.transfer.TransferConfig
                The transfer configuration to be used when performing
                the copy.
        """

        try:
            self.client.copy(
                CopySource=copy_source,
                Bucket=bucket, Key=key,
                **kwargs
            )

        except Exception as error:
            raise AwsClientException(error) from error

    def delete_object(
        self,
        bucket: str,
        key: str,
        **kwargs
    ) -> Dict:
        """
        Delete objects from a bucket using a single request...
        https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/s3/client/delete_object.html

        :param bucket: The bucket name of the bucket containing the object.
        :param key: Key name of the object to delete.
        :param kwargs:

        :return:

            .. code-block:: python

                {
                    "DeleteMarker": True|False,
                    "VersionId": "string",
                    "RequestCharged": "requester"
                }
            ..
        """

        try:
            return self.client.delete_object(
                Bucket=bucket,
                Key=key,
                **kwargs)

        except ClientError as error:
            raise AwsClientException(error) from error

    def delete_objects(
        self,
        bucket: str,
        objects: List[Dict],
        **kwargs
    ) -> Dict:
        """
        Delete objects from a bucket using a single request...
        https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/s3/client/delete_objects.html

        :param bucket:
        :param objects: The objects to delete...
            Object Identifier is unique value to identify objects.
            Key (string) [REQUIRED] -> Key name of the object to delete.
            VersionId (string) -> VersionId for the specific version of the object to delete.

            Example...

                .. code-block:: python

                    [{
                        "Key": "some_file.csv",
                        "VersionId": "6LGg7gQLhY41.maGB5Z6SWW.dcq0vx7b",
                    }]
                ..

        :param kwargs:

        :return:

            .. code-block:: python

                {
                    "Deleted": [
                        {
                            "Key": "string",
                            "VersionId": "string",
                            "DeleteMarker": True|False,
                            "DeleteMarkerVersionId": "string"
                        },
                    ],
                    "RequestCharged": "requester",
                    "Errors": [
                        {
                            "Key": "string",
                            "VersionId": "string",
                            "Code": "string",
                            "Message": "string"
                        },
                    ]
                }
            ..
        """

        if not objects:
            return {}

        try:
            return self.client.delete_objects(
                Bucket=bucket,
                Delete={"Objects": objects},
                **kwargs)

        except Exception as error:
            raise AwsClientException(error) from error
