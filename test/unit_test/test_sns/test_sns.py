# from moto_test.src.motowrapper.context import TestEnvContext
# from moto_test.src.motowrapper.wrapper import AWSResourceInitializer
import pytest

from aws_lambda_powertools.logging import Logger

from src.aws_moto_wrapper.context import TestEnvContext
from src.aws_moto_wrapper.wrapper import AWSResourceInitializer

logger = Logger()

def test_moto_read_sns(test_manager, sns_mock, sqs_mock):

    res_out_validator = test_manager.mock_env('test/input/test_sns/test_sns.yaml')

    sns_obj = TestEnvContext.get_sns_resource('moto_test_multi_msg_sns.fifo')
    sns_mock.publish(TopicArn=sns_obj['TopicArn'],
                     Message='{"key": "sns message 1", "bucket": "s3_bucket_name"}',
                     MessageGroupId='3321-2221-3321-3211',MessageDeduplicationId='1')
    sns_mock.publish(TopicArn=sns_obj['TopicArn'],
                     Message='{"key": "sns message 2", "bucket": "s3_bucket_name"}',
                     MessageGroupId='3321-2221-3321-3212', MessageDeduplicationId='1')
    logger.info("Message has been sent")

    res_out_validator.validate_out('multi_message_validate')


def test_moto_sns_single_message_lambda(test_manager, sns_mock, sqs_mock):
    res_out_validator = test_manager.mock_env('test/input/test_sns/test_sns.yaml')
    sns_obj = TestEnvContext.get_sns_resource('moto_test_single_msg_sns.fifo')
    sns_mock.publish(TopicArn=sns_obj['TopicArn'],
                     Message='{"key": "Single message", "bucket": "s3_bucket_name"}',
                     MessageGroupId='3321-2221-3321-3211',MessageDeduplicationId='1')
    logger.info("Message has been sent")

    res_out_validator.validate_out('single_message_validate')


def test_moto_sns_missing_message_lambda(test_manager, sns_mock, sqs_mock):
    res_out_validator = test_manager.mock_env('test/input/test_sns/test_sns.yaml')

    with pytest.raises(AssertionError) as exc_info:
        res_out_validator.validate_out('missing_message_validate')
    assert exc_info.value.args[0] =='No messages published by moto_test_missing_msg_sns.fifo'


def test_moto_sns_msg_count_not_matched(test_manager, sns_mock, sqs_mock):
    res_out_validator = test_manager.mock_env('test/input/test_sns/test_sns.yaml')
    sns_obj = TestEnvContext.get_sns_resource('moto_test_message_count_not_matched_sns')
    sns_mock.publish(TopicArn=sns_obj['TopicArn'],
                     Message='{"key": "msg 1", "bucket": "s3_bucket_name"}',)
    logger.info("Message has been sent")

    with pytest.raises(AssertionError) as exc_info:
        res_out_validator.validate_out('mess_count_not_matched')
    assert exc_info.value.args[0] == 'For moto_test_message_count_not_matched_sns,' \
                                     ' expected number of messages are 2, found 1'


def test_moto_sns_msg_not_matched(test_manager, sns_mock, sqs_mock):
    res_out_validator = test_manager.mock_env('test/input/test_sns/test_sns.yaml')
    sns_obj = TestEnvContext.get_sns_resource('moto_test_message_not_matched_sns')
    sns_mock.publish(TopicArn=sns_obj['TopicArn'],
                     Message='{"key": "Other message", "bucket": "s3_bucket_name"}',
                     MessageGroupId='3321-2221-3321-3211',MessageDeduplicationId='1')
    logger.info("Message has been sent")

    with pytest.raises(AssertionError) as exc_info:
        res_out_validator.validate_out('mess_not_matched')

    assert exc_info.value.args[0] == "For moto_test_message_not_matched_sns message not matched with expected, acc: " \
                                     "[{'key': 'Other message', 'bucket': 's3_bucket_name'}], exp: [{'key': 'msg 1', " \
                                     "'bucket': 's3_bucket_name'}]"
