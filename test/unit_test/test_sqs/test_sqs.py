# from moto_test.src.motowrapper.context import TestEnvContext
# from moto_test.src.motowrapper.wrapper import AWSResourceInitializer
import pytest

from aws_lambda_powertools.logging import Logger

from src.aws_moto_wrapper.context import TestEnvContext
from src.aws_moto_wrapper.wrapper import AWSResourceInitializer

logger = Logger()

def test_moto_read_s3(test_manager, sns_mock, sqs_mock):

    res_out_validator = test_manager.mock_env('test/input/test_sqs/test_sqs.yaml')

    sns_obj = TestEnvContext.get_sns_resource('bpDipDemo_Multi_msg.fifo')

    res_out_validator.validate_out('multi_message_validate')