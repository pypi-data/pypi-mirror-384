# -*- coding: utf-8 -*-

"""
AWS Systems Manager (SSM) Parameter Store client wrapper.

This module provides a high-level interface for interacting with AWS Systems
Manager Parameter Store, including support for retrieving parameters, secrets,
and managing parameter hierarchies.
"""

import inspect
from typing import Any, Dict, Iterator, List

from core_aws.services.base import AwsClient
from core_aws.services.base import AwsClientException
from core_aws.typing import SSMParameter


class SsmClient(AwsClient):
    """
    Client for AWS Systems Manager (SSM) Parameter Store.

    This client provides methods for retrieving, storing, and managing
    parameters in AWS Systems Manager Parameter Store. It supports:

    - Individual parameter retrieval with decryption
    - Bulk parameter retrieval by path hierarchy
    - Integration with AWS Secrets Manager
    - Parameter creation and updates
    - Object attribute population from SSM parameters

    Example:
        .. code-block:: python

            # Initialize client
            ssm = SsmClient(region="us-east-1")

            # Get a single parameter
            param = ssm.get_parameter("/myapp/database/host")
            print(param["Value"])

            # Get all parameters under a path
            for param in ssm.get_parameters_by_path("/myapp/"):
                print(f"{param['Name']}: {param['Value']}")

            # Retrieve a secret from Secrets Manager
            secret = ssm.get_secret("my-database-password")
        ..
    """

    client: "mypy_boto3_ssm.client.SSMClient"  # type: ignore[name-defined]

    def __init__(self, region: str, **kwargs: Any) -> None:
        """
        Initialize the SSM client.

        :param region: AWS region name (e.g., 'us-east-1', 'eu-west-1').
        :param kwargs: Additional arguments passed to boto3.client().
        """
        super().__init__("ssm", region_name=region, **kwargs)

    def get_secret(self, secret_id: str) -> str:
        """
        Retrieve a secret value from AWS Secrets Manager
        via SSM Parameter Store. This method uses SSM's special
        reference format to access secrets stored
        in AWS Secrets Manager: `/aws/reference/secretsmanager/{secret_id}`.

        :param secret_id: The ID or name of the secret in Secrets Manager.
        :return: The decrypted secret value as a string.

        :raises AwsClientException: If the secret cannot be retrieved.

        Example:
            .. code-block:: python

                ssm = SsmClient(region="us-east-1")
                db_password = ssm.get_secret("prod/database/password")
                print(f"Password: {db_password}")
            ..
        """

        try:
            return self.get_parameter(
                parameter_name=f"/aws/reference/secretsmanager/{secret_id}",
                with_decryption=True
            ).get("Value", "")

        except Exception as error:
            raise AwsClientException(error) from error

    def get_parameter(
        self,
        parameter_name: str,
        with_decryption: bool = True
    ) -> SSMParameter:
        """
        Retrieve a parameter from SSM Parameter Store. Retrieves information
        about a single parameter including its value, type, version, and
        metadata. Supports automatic decryption of SecureString
        parameters.

        Reference:
            https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ssm/client/get_parameter.html

        :param parameter_name:
            The fully qualified name of the parameter you want to query.
            Must include the complete hierarchy path (e.g., '/myapp/database/host').

        :param with_decryption:
            Return decrypted values for SecureString parameters. This flag
            is ignored for String and StringList parameter types.
            Default: True.

        :return: SSMParameter dictionary containing parameter information.

        :raises AwsClientException: If the parameter cannot be retrieved.

        Example:
            .. code-block:: python

                ssm = SsmClient(region="us-east-1")

                # Get a standard parameter
                param = ssm.get_parameter("/myapp/config/api_url")
                print(param["Value"])  # "https://api.example.com"

                # Get a SecureString parameter (auto-decrypted)
                secret_param = ssm.get_parameter("/myapp/secrets/api_key")
                print(secret_param["Type"])  # "SecureString"

                # Get without decryption
                encrypted = ssm.get_parameter(
                    "/myapp/secrets/api_key",
                    with_decryption=False
                )
            ..

        Return Structure:
            .. code-block:: python

                {
                    "Name": "string",
                    "Type": "String"|"StringList"|"SecureString",
                    "Value": "string",
                    "Version": 123,
                    "Selector": "string",
                    "SourceResult": "string",
                    "LastModifiedDate": datetime(2015, 1, 1),
                    "ARN": "string",
                    "DataType": "string"
                }
            ..
        """

        try:
            response = self.client.get_parameter(
                Name=parameter_name,
                WithDecryption=with_decryption)

            return response["Parameter"]

        except Exception as error:
            raise AwsClientException(error) from error

    def get_parameters_by_path(
        self,
        path: str,
        with_decryption: bool = True,
        **kwargs: Any
    ) -> Iterator[SSMParameter]:
        """
        Retrieve all parameters under a specific path hierarchy. Recursively
        retrieves parameters from a path in SSM Parameter Store, automatically
        handling pagination. This is useful for fetching multiple related
        parameters at once (e.g., all database configuration
        parameters under `/myapp/database/`).

        Reference:
            https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ssm/client/get_parameters_by_path.html

        :param path:
            The parameter path hierarchy. Hierarchies start with a forward
            slash (/) and can have up to 15 levels. Examples:

            - ``/myapp/`` - gets all parameters under myapp
            - ``/myapp/database/`` - gets all database parameters
            - ``/prod/api/config/`` - gets all production API configs

        :param with_decryption:
            Retrieve all parameters with their values decrypted (for
            SecureString types). Default: True.

        :param kwargs:
            Additional boto3 parameters:

            - **Recursive** (bool):
                Retrieve all parameters within the hierarchy, not just
                immediate children. Default: False.

            - **ParameterFilters** (list):
                Filters to limit results. List of dicts with keys:
                  - Key (string): Filter key (e.g., 'Type', 'Name')
                  - Option (string): Filter option (e.g., 'Equals', 'BeginsWith')
                  - Values (list): Values to match

            - **MaxResults** (int):
                Maximum number of items per API call (1-10). Pagination
                continues automatically regardless of this value.

        :return:
            Iterator yielding SSMParameter dictionaries. Automatically
            handles pagination across multiple API calls.

        :raises AwsClientException: If parameters cannot be retrieved.

        Example:
            .. code-block:: python

                ssm = SsmClient(region="us-east-1")

                # Get all parameters under a path
                for param in ssm.get_parameters_by_path("/myapp/database/"):
                    print(f"{param['Name']}: {param['Value']}")

                # Get all parameters recursively
                for param in ssm.get_parameters_by_path(
                    "/myapp/",
                    Recursive=True
                ):
                    print(f"{param['Name']}: {param['Value']}")

                # Filter by type
                for param in ssm.get_parameters_by_path(
                    "/myapp/",
                    ParameterFilters=[
                        {
                            "Key": "Type",
                            "Option": "Equals",
                            "Values": ["SecureString"]
                        }
                    ]
                ):
                    print(f"Secret: {param['Name']}")
            ..

        Return Structure:
            Each yielded item has the structure:

            .. code-block:: python

                {
                    "Name": "string",
                    "Type": "String"|"StringList"|"SecureString",
                    "Value": "string",
                    "Version": 123,
                    "Selector": "string",
                    "SourceResult": "string",
                    "LastModifiedDate": datetime(2015, 1, 1),
                    "ARN": "string",
                    "DataType": "string"
                }
            ..
        """

        try:
            while True:
                response = self.client.get_parameters_by_path(
                    Path=path,
                    WithDecryption=with_decryption,
                    **kwargs)

                yield from response.get("Parameters", [])
                next_token = response.get("NextToken")
                if not next_token:
                    return

                kwargs["NextToken"] = next_token

        except Exception as error:
            raise AwsClientException(error) from error

    def put_parameter(
        self,
        name: str,
        value: str,
        overwrite: bool = False,
        **kwargs: Any
    ) -> Dict[str, Any]:
        """
        Create or update a parameter in SSM Parameter Store. Adds a new
        parameter or updates an existing one in Parameter Store. Supports
        standard, advanced, and intelligent-tiering parameters with
        optional encryption for SecureString types.

        Reference:
            https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ssm.html#SSM.Client.put_parameter

        :param name:
            The fully qualified name of the parameter. Must include the
            complete hierarchy path with leading forward slash (/).
            Example: `/Dev/DBServer/MySQL/db-string13`

        :param value:
            The parameter value. Standard parameters support up to 4 KB,
            advanced parameters support up to 8 KB.

        :param overwrite:
            Overwrite an existing parameter. If False and parameter exists,
            raises an error. Default: False.

        :param kwargs:
            Additional boto3 parameters:

            - **Description** (str):
                Information about the parameter. Optional but recommended.

            - **Type** (str):
                Parameter type: 'String', 'StringList', or 'SecureString'.
                Default: 'String'.

            - **KeyId** (str):
                KMS key ID for encrypting SecureString parameters. Uses
                default AWS account key if not specified. Required for
                SecureString type.

            - **AllowedPattern** (str):
                Regex pattern to validate parameter value.
                Example: `^\\d+$` for numbers only.

            - **Tags** (list):
                Resource tags. List of dicts with 'Key' and 'Value'.

            - **Tier** (str):
                'Standard', 'Advanced', or 'Intelligent-Tiering'.
                Default: 'Standard'.

            - **DataType** (str):
                Data type hint (e.g., 'text', 'aws:ec2:image').

        :return:
            Dictionary containing version and tier information.

        :raises AwsClientException: If parameter creation/update fails.

        Example:
            .. code-block:: python

                ssm = SsmClient(region="us-east-1")

                # Create a simple parameter
                result = ssm.put_parameter(
                    name="/myapp/config/api_url",
                    value="https://api.example.com"
                )
                print(f"Version: {result['Version']}")

                # Create a SecureString parameter
                ssm.put_parameter(
                    name="/myapp/secrets/api_key",
                    value="secret-key-12345",
                    Type="SecureString",
                    Description="API key for external service"
                )

                # Update an existing parameter
                ssm.put_parameter(
                    name="/myapp/config/api_url",
                    value="https://new-api.example.com",
                    overwrite=True
                )

                # Create with tags
                ssm.put_parameter(
                    name="/myapp/config/version",
                    value="1.0.0",
                    Tags=[
                        {"Key": "Environment", "Value": "Production"},
                        {"Key": "Application", "Value": "MyApp"}
                    ]
                )
            ..

        Return Structure:
            .. code-block:: python

                {
                    "Version": 123,
                    "Tier": "Standard" | "Advanced" | "Intelligent-Tiering"
                }
            ..
        """

        try:
            return self.client.put_parameter(
                Name=name,
                Value=value,
                Overwrite=overwrite,
                **kwargs)

        except Exception as error:
            raise AwsClientException(error) from error

    def retrieve_parameters_from_ssm(
        self,
        ssm_path: str,
        parameters: List[str],
    ) -> Dict[str, str]:
        """
        Retrieve specific parameters from SSM by matching suffixes. Retrieves all
        parameters under a path and returns a dictionary mapping parameter
        suffixes to their values. This is useful when you know the
        parameter suffixes but not the full paths.

        :param ssm_path:
            SSM path to search for parameters (e.g., '/myapp/database/').

        :param parameters:
            List of parameter name suffixes to extract. Each suffix will
            be matched against the end of parameter names.
            Example: ['host', 'port', 'username']

        :return:
            Dictionary mapping parameter suffixes to their values.
            Returns empty string for suffixes not found.

        Example:
            .. code-block:: python

                ssm = SsmClient(region="us-east-1")

                # Retrieve specific database parameters
                db_params = ssm.retrieve_parameters_from_ssm(
                    ssm_path="/myapp/database/",
                    parameters=["host", "port", "username"]
                )
                # Result: {
                #   "host": "db.example.com",
                #   "port": "5432",
                #   "username": "admin"
                # }

                print(f"Database: {db_params['host']}:{db_params['port']}")
            ..

        Warning:
            This method has O(n*m) complexity where n=number of parameters
            in SSM path and m=number of suffixes. For large parameter sets,
            consider using `get_parameters_by_path()` directly and filtering
            results manually for better performance.
        """

        results: Dict[str, str] = {}
        all_params = list(self.get_parameters_by_path(ssm_path))

        for suffix in parameters:
            for param in all_params:
                param_name = param.get("Name", "")
                if param_name.endswith(suffix):
                    results[suffix] = param.get("Value", "")
                    break

        return results

    def update_obj_attrs(self, obj: object, ssm_path: str) -> None:
        """
        Update object attributes with values from SSM Parameter Store. Scans
        object attributes and replaces their values with matching SSM parameter
        values. The current attribute value is treated as
        the SSM parameter name to look up.

        :param obj:
            Object whose attributes will be updated. Must have public
            (non-underscore) attributes.

        :param ssm_path:
            SSM path to retrieve parameters from (e.g., '/myapp/config/').

        Example:
            .. code-block:: python

                class DatabaseConfig:
                    def __init__(self):
                        self.host = "/myapp/database/host"
                        self.port = "/myapp/database/port"
                        self.username = "/myapp/database/username"

                ssm = SsmClient(region="us-east-1")
                config = DatabaseConfig()

                # Before: config.host = "/myapp/database/host"
                ssm.update_obj_attrs(config, "/myapp/database/")
                # After: config.host = "db.example.com"

                print(config.host)  # "db.example.com"
                print(config.port)  # "5432"
            ..

        Warning:
            This method has O(n*m) complexity where n=number of SSM parameters
            and m=number of object attributes. Use with caution on large
            objects or parameter sets.

        Note:
          - Only public attributes (not starting with '_') are updated
          - Methods and callable attributes are skipped
          - Attribute value must exactly match the SSM parameter name
        """

        all_params = list(self.get_parameters_by_path(ssm_path))
        param_map = {p.get("Name", ""): p.get("Value", "") for p in all_params}

        for attr_name, attr_value in inspect.getmembers(obj):
            # Skip private attributes and methods...
            if attr_name.startswith("_") or inspect.ismethod(attr_value):
                continue

            if attr_value in param_map:
                setattr(obj, attr_name, param_map[attr_value])
