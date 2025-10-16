# -*- coding: utf-8 -*-

from unittest.mock import patch

import botocore.session
from core_tests.tests.base import BaseTestCase

from core_aws.typing import ClientContext
from core_aws.typing import CognitoIdentity
from core_aws.typing import LambdaContext
from core_aws.typing import MobileClient


class BaseAwsTestCase(BaseTestCase):
    """ Base class for Test Cases related to AWS and boto3 """

    aws_patcher = patch("botocore.client.BaseClient._make_api_call")
    aws_client_mock = None

    @classmethod
    def setUpClass(cls) -> None:
        super(BaseAwsTestCase, cls).setUpClass()
        cls.aws_client_mock = cls.aws_patcher.start()
        cls.aws_client_mock.side_effect = cls._make_api_call

    @classmethod
    def tearDownClass(cls) -> None:
        super(BaseAwsTestCase, cls).tearDownClass()
        cls.aws_patcher.stop()

    @staticmethod
    def _make_api_call(operation_name, api_params):
        """
        Each class can implement the response depending
        on the services they are patching.
        """

    @staticmethod
    def sample_context() -> LambdaContext:
        return LambdaContext(
            function_name="Lambda-Function-Name",
            function_version="$LATEST",
            invoked_function_arn="arn:aws:lambda:us-east-1:******:function:Lambda-Function-Name",
            memory_limit_in_mb=128,
            aws_request_id="65e839d8-650a-4803-8c08-1d7fcc62cc5e",
            log_group_name="/aws/lambda/Lambda-Function-Name",
            log_stream_name="2021/05/03/[$LATEST]34cc5b8a888241b383ff071d82520797",
            identity=CognitoIdentity(
                cognito_identity_id="some-id",
                cognito_identity_pool_id="some-pool-id"
            ),
            client_context=ClientContext(
                client=MobileClient(
                    installation_id="some-inst-id",
                    app_title="Some-App",
                    app_version_name="some-version",
                    app_version_code="x01zT",
                    app_package_name="app-pkg"
                ),
                custom={},
                env={},
            ),
        )

    @staticmethod
    def generate_error(
        service: str = "ssm",
        region_name: str = "us-east-1",
        operation_name: str = "GetParameter",
        error_code: str = "ParameterNotFound",
        error_message: str = "The parameter was not found.",
    ) -> Exception:
        """ Generate a botocore client exception for testing. """

        error_response = {
            "Error": {
                "Code": error_code,
                "Message": error_message,
            },
        }

        client = botocore.session.get_session().create_client(
            service_name=service,
            region_name=region_name)

        exception_class = getattr(client.exceptions, error_code)

        return exception_class(
            error_response=error_response,
            operation_name=operation_name,
        )
