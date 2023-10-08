import pytest
from aws_lambda_powertools.logging import Logger
from src.aws_moto_wrapper.context import TestEnvContext

logger = Logger()

def test_moto_read_sqs(test_manager, sqs_mock):
    res_out_validator = test_manager.mock_env('test/input/test_sqs/test_sqs.yaml')
    sqs_obj = TestEnvContext.get_sqs_resource('moto_test_multi_msg_sqs.fifo')
    sqs_mock.send_message(
        QueueUrl=sqs_obj["QueueUrl"],
        MessageBody='{"key": "sqs message 1", "bucket": "s3_bucket_name"}',
        MessageGroupId='3321-2221-3321-3211',
        MessageDeduplicationId='1'
    )
    sqs_mock.send_message(
        QueueUrl=sqs_obj["QueueUrl"],
        MessageBody='{"key": "sqs message 2", "bucket": "s3_bucket_name"}',
        MessageGroupId='3321-2221-3321-3211',
        MessageDeduplicationId='2'
    )
    logger.info("Message has been sent")
    res_out_validator.validate_out('multi_message_validate')
    
    
def test_moto_sqs_single_message_lambda(test_manager, sqs_mock):
    res_out_validator = test_manager.mock_env('test/input/test_sqs/test_sqs.yaml')
    sqs_obj = TestEnvContext.get_sqs_resource('moto_test_single_msg_sqs.fifo')
    sqs_mock.send_message(
        QueueUrl=sqs_obj["QueueUrl"],
        MessageBody='{"key": "Single message", "bucket": "s3_bucket_name"}',
        MessageGroupId='3321-2221-3321-3211',
        MessageDeduplicationId='1'
    )
    logger.info("Message has been sent")
    res_out_validator.validate_out('single_message_validate')
   
    
def test_moto_sqs_missing_message_lambda(test_manager):
    res_out_validator = test_manager.mock_env('test/input/test_sqs/test_sqs.yaml')
    with pytest.raises(AssertionError) as exc_info:
        res_out_validator.validate_out('missing_message_validate_sqs')
    assert exc_info.value.args[0] =='No messages published by moto_test_missing_msg_sqs.fifo'
 
    
def test_moto_sqs_msg_count_not_matched(test_manager, sqs_mock):
    res_out_validator = test_manager.mock_env('test/input/test_sqs/test_sqs.yaml')
    sqs_obj = TestEnvContext.get_sqs_resource('moto_test_message_count_not_matched_sqs')
    sqs_mock.send_message(
        QueueUrl=sqs_obj["QueueUrl"],
        MessageBody='{"key": "msg 1", "bucket": "s3_bucket_name"}',
    )
    logger.info("Message has been sent")

    with pytest.raises(AssertionError) as exc_info:
        res_out_validator.validate_out('mess_count_not_matched')
    assert exc_info.value.args[0] == 'For moto_test_message_count_not_matched_sqs,' \
                                     ' expected number of messages are 2, found 1'


def test_moto_sqs_msg_not_matched(test_manager, sqs_mock):
    res_out_validator = test_manager.mock_env('test/input/test_sqs/test_sqs.yaml')
    sqs_obj = TestEnvContext.get_sqs_resource('moto_test_message_not_matched_sqs')
    sqs_mock.send_message(
        QueueUrl=sqs_obj["QueueUrl"],
        MessageBody='{"key": "Other message", "bucket": "s3_bucket_name"}',
        MessageGroupId='3321-2221-3321-3211',
        MessageDeduplicationId='1'
    )
    logger.info("Message has been sent")

    with pytest.raises(AssertionError) as exc_info:
        res_out_validator.validate_out('mess_not_matched')

    assert exc_info.value.args[0] == "For moto_test_message_not_matched_sqs message not matched with expected, acc: " \
                                     "[{'key': 'Other message', 'bucket': 's3_bucket_name'}], exp: [{'key': 'msg 1', " \
                                     "'bucket': 's3_bucket_name'}]"