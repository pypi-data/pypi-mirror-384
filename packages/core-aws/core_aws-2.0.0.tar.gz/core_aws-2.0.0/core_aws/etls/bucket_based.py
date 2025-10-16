# -*- coding: utf-8 -*-

import os
from abc import ABC, abstractmethod
from typing import Any, Iterator, Optional

from core_etl.file_based import IBaseEtlFromFile

from core_aws.etls.base import IBaseEtlOnAWS


class IBaseEtlOnAwsBucket(IBaseEtlFromFile, IBaseEtlOnAWS, ABC):
    """
    Base class for ETL processes that retrieve and process files from AWS S3.

    This class provides a framework for ETL processes that:
    - Download files from an S3 bucket
    - Process files locally
    - Archive successfully processed files to an archive bucket
    - Move failed files to an error bucket
    - Clean up local and source files after processing

    The workflow for each file:
    1. Download from source bucket to local temp folder
    2. Process the file locally (via process_local_file)
    3. On success: copy to archive_bucket/archive_prefix
    4. On error: copy to error_bucket/error_prefix
    5. Delete from source bucket
    6. Delete local temp file

    Example:
        .. code-block:: python

            class MyS3ETL(IBaseEtlOnAwsBucket):
                def process_local_file(self, local_path: str):
                    # Process the downloaded file
                    with open(local_path, 'r') as f:
                        data = f.read()
                        # ... process data ...

            etl = MyS3ETL(
                bucket="my-source-bucket",
                prefix="incoming/",
                archive_bucket="my-archive-bucket",
                archive_prefix="processed/",
                error_bucket="my-error-bucket",
                error_prefix="failed/"
            )
            etl.execute()
        ..
    """

    def __init__(
        self,
        bucket: Optional[str] = None,
        prefix: Optional[str] = None,
        archive_bucket: Optional[str] = None,
        archive_prefix: Optional[str] = None,
        error_bucket: Optional[str] = None,
        error_prefix: Optional[str] = None,
        **kwargs: Any
    ) -> None:
        """
        Initialize the S3-based ETL process.

        :param bucket: Source S3 bucket containing files to process.
        :param prefix: Path/prefix within the source bucket to retrieve files from.
        :param archive_bucket: S3 bucket for archiving successfully processed files (optional).
        :param archive_prefix: Path/prefix to use when archiving successful files (optional).
        :param error_bucket: S3 bucket for archiving files that failed processing (optional).
        :param error_prefix: Path/prefix to use when archiving failed files (optional).
        :param kwargs: Additional arguments passed to parent classes.

        Note:
            - Files are always deleted from the source bucket after processing.
            - If archive_bucket/error_bucket are not provided, files won't be archived.
            - Source files are deleted regardless of archiving success/failure.
        """

        super().__init__(**kwargs)

        self.bucket = bucket
        self.archive_bucket = archive_bucket
        self.error_bucket = error_bucket

        self.prefix = prefix
        self.archive_prefix = archive_prefix
        self.error_prefix = error_prefix

    def _execute(self, *args: Any, **kwargs: Any) -> int:
        """
        Execute the ETL process for all files in the S3 bucket.

        :param args: Positional arguments passed to parent _execute.
        :param kwargs: Keyword arguments passed to parent _execute.

        :return: Number of files processed.
        """

        self.info(f"Retrieving files from bucket: {self.bucket}, path: {self.prefix}...")
        return super()._execute(*args, **kwargs)

    def get_paths(self, *args: Any, **kwargs: Any) -> Iterator[str]:
        """
        Retrieve S3 object keys (file paths) from the source bucket. Yields
        object keys from the configured bucket and prefix that will be
        downloaded and processed.

        :param args: Positional arguments (unused).
        :param kwargs: Keyword arguments (unused).

        :return: Iterator of S3 object keys (file paths).
        """

        if not self.bucket:
            raise ValueError("bucket must be configured")

        if not self.prefix:
            raise ValueError("prefix must be configured")

        for rec in self.s3_client.list_all_objects(self.bucket, self.prefix):
            yield rec["Key"]

    def process_file(self, path: str, *args: Any, **kwargs: Any) -> None:
        """
        Download, process, archive, and clean up a single file from S3.

        This method orchestrates the complete workflow for a single file:
        1. Downloads the file from S3 to local temp folder
        2. Calls process_local_file() to process it
        3. Archives to success/error bucket based on processing result
        4. Deletes the file from the source S3 bucket
        5. Deletes the local temp file

        :param path: S3 object key (file path) to process.
        :param args: Positional arguments (unused).
        :param kwargs: Keyword arguments (unused).
        """

        if not self.bucket:
            raise ValueError("bucket must be configured")

        self.info(f"Downloading file: {path}...")
        file_name = os.path.basename(path)

        local_path = self.s3_client.download_file(
            local_path=f"{self.temp_folder}/{file_name}",
            bucket=self.bucket,
            key=path)

        self.info("Downloaded!")
        final_bucket: Optional[str] = None
        final_path: Optional[str] = None

        try:
            self.info(f"Processing file: {file_name}.")
            self.process_local_file(local_path)
            self.info("Processed!")

        except Exception as error:
            self.error(f"Error processing file: {error}.")
            final_bucket = self.error_bucket
            final_path = self.error_prefix

        else:
            final_bucket = self.archive_bucket
            final_path = self.archive_prefix

        finally:
            # Archive to appropriate bucket (success or error)
            if final_bucket and final_path:
                self.info(f"Archiving into bucket: {final_bucket}, path: {final_path}...")

                try:
                    self.s3_client.copy(
                        copy_source={
                            "Bucket": self.bucket,
                            "Key": path
                        },
                        bucket=final_bucket,
                        key=final_path,
                    )

                    self.info("Archived successfully!")

                except Exception as archive_error:
                    self.error(f"Failed to archive file: {archive_error}")

            else:
                self.info("Skipping archiving (no destination bucket configured).")

            # Deleting from source bucket...
            try:
                self.info(f"Deleting file: {path} from bucket: {self.bucket}...")
                self.s3_client.delete_object(self.bucket, key=path)
                self.info("File deleted from S3!")

            except Exception as delete_error:
                self.error(f"Failed to delete file from S3: {delete_error}")

            # Deleting local temporal file...
            try:
                if os.path.exists(local_path):
                    os.remove(local_path)
                    self.info(f"Local temp file deleted: {local_path}")

            except Exception as local_delete_error:
                self.error(f"Failed to delete local file: {local_delete_error}")

    @abstractmethod
    def process_local_file(self, local_path: str, *args: Any, **kwargs: Any) -> None:
        """
        Process a downloaded file from the local filesystem. This abstract
        method must be implemented by subclasses to define
        the actual processing logic for each file.

        :param local_path: Absolute path to the downloaded file in the temp folder.
        :param args: Additional positional arguments.
        :param kwargs: Additional keyword arguments.

        :raises Exception:
            Any exception raised will cause the file to be archived to
            the error bucket instead of the archive bucket.

        Example:
            .. code-block:: python

                def process_local_file(self, local_path: str):
                    with open(local_path, 'r') as f:
                        data = json.load(f)
                        # Process data...
                        self.database.insert(data)
            ..
        """
