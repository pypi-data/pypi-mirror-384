# -*- coding: utf-8 -*-

import json
from abc import ABC
from typing import Any, List, Optional

from core_etl.base import IBaseETL

from core_aws.services.base import AwsClientException
from core_aws.services.s3.client import S3Client
from core_aws.services.sqs.client import SqsClient
from core_aws.services.ssm.client import SsmClient
from core_aws.typing import SSMParameter


class IBaseEtlOnAWS(IBaseETL, ABC):
    """
    Base class for ETL tasks executed on AWS. It provides common
    features that can be used into the ETL processes running
    on AWS services.

    Provides common features that can be used in ETL processes, including:
      - Automatic parameter loading from AWS Systems Manager Parameter Store.
      - JSON attribute parsing.
      - Pre-configured AWS service clients (SSM, SQS, S3).
      - Validation of required attributes.
      - Configurable strict/lenient validation modes.

    Example:
        .. code-block:: python

            class MyETL(IBaseEtlOnAWS):
                def __init__(self):
                    self.database_url = "/myapp/prod/database"
                    self.api_config = '{"timeout": 30}'

                    super().__init__(
                        aws_region="us-east-1",
                        ssm_parameters_path="/myapp/prod",
                        attrs_to_update=["database_url"],
                        json_attrs=["api_config"],
                        strict_ssm_validation=True
                    )

                def extract(self):
                    # database_url now contains the actual value from SSM
                    # api_config is now a dict: {"timeout": 30}
                    pass
        ..
    """

    def __init__(
        self,
        aws_region: str,
        ssm_parameters_path: Optional[str] = None,
        attrs_to_update: Optional[List[str]] = None,
        json_attrs: Optional[List[str]] = None,
        ssm_endpoint_url: Optional[str] = None,
        strict_ssm_validation: bool = False,
        **kwargs: Any
    ) -> None:
        """
        Initialize the AWS ETL base class.

        :param aws_region: AWS Region (e.g., "us-east-1", "eu-west-1").
        :param ssm_parameters_path: Path where parameters can be found in SSM Parameter Store.

        :param attrs_to_update:
            List of object attributes to update from SSM parameters. Attribute
            values should contain SSM parameter paths.

        :param json_attrs:
            List of attributes that should be parsed as JSON (dicts, lists).
        
        :param ssm_endpoint_url:
            Custom endpoint URL for SSM service (useful for testing/LocalStack).

        :param strict_ssm_validation:
            If True, raises exceptions when expected SSM parameters are
            missing. If False (default), logs warnings instead.

        :param kwargs: Additional arguments passed to the parent IBaseETL class.

        :raises AttributeError:
            If specified attributes don't exist on the object during pre_processing.
        
        :raises AwsClientException:
            If strict_ssm_validation=True and SSM parameters are missing.
        """

        super().__init__(**kwargs)

        self.aws_region = aws_region
        self.ssm_parameters_path = ssm_parameters_path
        self.strict_ssm_validation = strict_ssm_validation
        self.attrs_to_update = attrs_to_update or []
        self.json_attrs = json_attrs or []

        # Some useful clients to have. We could add more if required...
        ssm_args = {"endpoint_url": ssm_endpoint_url} if ssm_endpoint_url else {}

        self.ssm_client = SsmClient(region=self.aws_region, **ssm_args)
        self.sqs_client = SqsClient(region=self.aws_region)
        self.s3_client = S3Client()

    def pre_processing(self, **kwargs: Any) -> None:
        """
        Pre-processing hook that validates attributes, updates them
        from SSM, and parses JSON.

        This method is called before ETL execution and performs the following:
          1. Validates that attrs_to_update and json_attrs exist on the object
          2. Retrieves parameters from SSM Parameter Store
          3. Updates object attributes with SSM values
          4. Parses JSON string attributes into Python objects

        :param kwargs:
            Additional arguments passed to the parent pre_processing method.

        :raises AttributeError: If json_attrs don't exist on the object.
        :raises AwsClientException:
            If strict_ssm_validation=True and parameters are missing/not found.

        :warns: If attrs_to_update don't exist or if JSON parsing fails.
        """

        super().pre_processing(**kwargs)

        missing_attrs = [attr for attr in self.attrs_to_update if not hasattr(self, attr)]
        if missing_attrs:
            self.warning(
                f"The following attributes don't exist on "
                f"the object: {missing_attrs}."
            )

        missing_json_attrs = [attr for attr in self.json_attrs if not hasattr(self, attr)]
        if missing_json_attrs:
            raise AttributeError(
                f"The following JSON attributes don't "
                f"exist: {missing_json_attrs}."
            )

        self._update_parameters(self.attrs_to_update)

        for attr in self.json_attrs:
            value = getattr(self, attr)
            if value:
                try:
                    setattr(self, attr, json.loads(value))

                except (json.JSONDecodeError, TypeError) as error:
                    self.warning(f"Failed to parse JSON for attribute '{attr}': {error}")

    def _update_parameters(self, attrs: List[str]) -> None:
        """
        Retrieve parameters from SSM Parameter Store and update
        object attributes. Fetches all parameters under ``ssm_parameters_path``
        and updates object attributes where the attribute value
        matches a parameter name in SSM.

        :param attrs: List of attribute names to update from SSM.

        :raises AwsClientException:
            If strict_ssm_validation=True and:
              - ssm_parameters_path is not configured
              - No parameters found at the specified path
              - Required parameters are missing

        :warns: If strict_ssm_validation=False and issues are detected.
        """

        if not attrs:
            self.info("No attributes to update from SSM.")
            return

        if not self.ssm_parameters_path:
            error = "The SSM path not configured, but it's expected!"
            if self.strict_ssm_validation:
                raise AwsClientException(error)

            self.warning(error)
            return

        self.info("Getting attributes from SSM Parameter Store service...")

        params = list(self.ssm_client.get_parameters_by_path(self.ssm_parameters_path))

        if not params:
            error = f"No parameters found at path: {self.ssm_parameters_path}."
            if self.strict_ssm_validation:
                raise AwsClientException(error)

            self.warning(error)
            return

        self._update_attributes(attributes=attrs, parameters=params)
        self.info("The attributes were updated!")

    def _update_attributes(
        self,
        attributes: List[str],
        parameters: List[SSMParameter],
    ) -> None:
        """
        Update object attributes using values from SSM Parameter Store. Matches
        object attribute values (which contain SSM parameter paths) against the parameter
        names retrieved from SSM, and replaces the attribute values
        with the actual parameter values.

        :param attributes: List of attribute names to update.
        :param parameters: List of SSM parameter dictionaries containing Name and Value.

        :raises AwsClientException: If strict_ssm_validation=True and parameters are missing.
        :warns: If strict_ssm_validation=False and parameters are missing.

        Example:
            Given an SSM parameter:

                .. code-block:: python

                    [{
                        "Name": "/path/service/user",
                        "Value": "user_name"
                    }]
                ..

            If the object has a "user" attribute with value "/path/service/user",
            the attribute will be updated to "user_name".
        """

        param_map = {
            param.get("Name"): param.get("Value")
            for param in parameters
            if param.get("Name") is not None
        }

        missing_params = []

        for attr in attributes:
            current_val = getattr(self, attr, None)
            if current_val and isinstance(current_val, str):
                if current_val in param_map:
                    setattr(self, attr, param_map[current_val])
                else:
                    missing_params.append((attr, current_val))

        if missing_params:
            error_msg = (
                f"Missing SSM parameters: "
                f"{', '.join([f'{attr}={path}' for attr, path in missing_params])}"
            )

            if self.strict_ssm_validation:
                raise AwsClientException(error_msg)

            self.warning(error_msg)
