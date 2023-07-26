import os
from typing import Callable
from uuid import uuid4
import boto3
import pytest
from moto import mock_sns, mock_sqs, mock_s3, mock_dynamodb2, mock_secretsmanager


@pytest.fixture(scope="module")
def sqs_event_factory() -> Callable:
    def factory(body: str):
        return {
            "messageId": "059f36b4-87a3-44ab-83d2-661975830a7d",
            "receiptHandle": "AQEBwJnKyrHigUMZj6rYigCgxlaS3SLy0a",
            "body": body,
            "attributes": {},
            "messageAttributes": {},
            "md5OfBody": "e4e68fb7bd0e697a0ae8f1bb342846b3",
            "eventSource": "aws:sqs",
            "eventSourceARN": "arn:aws:sqs:us-east-2:175050809122:my-queue",
            "awsRegion": "us-east-1",
        }

    return factory


class MockLambdaContext(object):
    def __init__(self, function_name):
        self.function_name = function_name
        self.function_version = "v$LATEST"
        self.memory_limit_in_mb = 512
        self.invoked_function_arn = (
            f"arn:aws:lambda:us-east-1:ACCOUNT:function:{self.function_name}"
        )
        self.aws_request_id = str(uuid4)


SNS_NAME = "TeamsAlertSNS"


@pytest.fixture(scope="module", autouse=True)
def mock_envs():
    """Mocked environments for testing."""
    os.environ["AWS_ACCESS_KEY_ID"] = "testing"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
    os.environ["AWS_SECURITY_TOKEN"] = "testing"
    os.environ["AWS_SESSION_TOKEN"] = "testing"
    os.environ["AWS_DEFAULT_REGION"] = "us-east-1"
    os.environ["POWERTOOLS_TRACE_DISABLED"] = "1"
    os.environ["POWERTOOLS_SERVICE_NAME"] = "dip-assignment"
    os.environ["POWERTOOLS_METRICS_NAMESPACE"] = "dsp"

    os.environ["PACKAGE_LOOKUP_TBL_NAME"] = "package_lookup_tbl"
    os.environ["HDS_SECRET_NAME"] = "hds.secretes"
    os.environ["NUMBER_OF_RETRIES"] = "2"
    os.environ["BACKOFF_IN_SECONDS"] = "1"
    os.environ["HDS_STOCK_BUCKET"] = "bp_dip_hds_stock"
    os.environ["SNS_NAME"] = "TeamsAlertSNS"
    os.environ["ERROR_ALERT_SNS"] = f"arn:aws:sns:us-east-1:123456789012:{SNS_NAME}"
    os.environ["ALERT_SUBJECT"] = "HDS"
    os.environ["MOTO_ACCOUNT_ID"] = "123456789012"
    os.environ["AWS_LAMBDA_FUNCTION_NAME"] = "hds_publish"



@pytest.fixture
def lambda_context():
    return MockLambdaContext("dummy_function")




