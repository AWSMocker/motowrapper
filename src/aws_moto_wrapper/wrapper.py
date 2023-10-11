from dataclasses import dataclass

import yaml
import json
import boto3
import pytest
from functools import partial

from dacite import from_dict
from moto import mock_s3
from yaml.loader import SafeLoader
from moto import mock_sns, mock_sqs, mock_dynamodb2


from .handler import env_creator, MotoWrapperContext

from aws_lambda_powertools import Logger

logger = Logger()


# Open the file and load the file
def __convert_to_json(file_location):
    with open(file_location) as f:
        return yaml.load(f, Loader=SafeLoader)


def __validate(sqs, s3, dynamodb, sns_mock, env_detail, json_stack, file_type='yaml'):
    logger.info('Validting.......')


def jsonfy_evn_details(env_detail, file_type):
    if file_type.lower() == "yaml":
        json_stack = __convert_to_json(env_detail)
    else:
        with open(env_detail) as f:
            json_stack = json.load(f)
    return json_stack


@pytest.fixture(scope="function")
def s3_mock():
    with mock_s3():
        logger.info("\n S3 Up....")
        yield boto3.client("s3")
        logger.info("\n S3 Down....")


@pytest.fixture(scope="function")
def sqs_mock():
    with mock_sqs():
        logger.info("\n SQS Up....")
        yield boto3.client("sqs")
        logger.info("\n SQS Down....")


@pytest.fixture(scope="function")
def dynamodb_mock():
    with mock_dynamodb2():
        logger.info("\n dynamoDB Up....")
        yield boto3.resource("dynamodb")
        logger.info("\n dynamoDB Down....")


@pytest.fixture(scope="function")
def sns_mock():
    with mock_sns():
        logger.info("\n SNS Up....")
        yield boto3.client("sns")
        logger.info("\n SNS  Down....")


class AWSResourceInitializer(object):

    def __init__(self, sqs_mock, s3_mock, dynamodb_mock, sns_mock):
        self.sqs_mock = sqs_mock
        self.sns_mock = sns_mock
        self.s3_mock = s3_mock
        self.dynamodb_mock = dynamodb_mock

    def mock_env(self, env_detail):
        self.env_detail = env_detail
        json_stack = jsonfy_evn_details(env_detail, 'yaml')

        setup_list = json_stack.get("setup")
        validate_resource = json_stack.get("validate")
        global_config = validate_resource.get('global')
        expected_testwise_res = validate_resource.get('expectedTestResourceOutput')
        test_name_to_exp_res = {item['name']:item for item in expected_testwise_res}
        wrapper_context = MotoWrapperContext(sqs=self.sqs_mock, s3=self.s3_mock, dynamodb=self.dynamodb_mock,
                                             env_in_json=setup_list, sns=self.sns_mock,
                                             test_name_to_exp_res=test_name_to_exp_res,global_config=global_config)
        env_creator.prepare_env(wrapper_context)

        return ResourceOutputValidator(wrapper_context, env_creator.initiator_handler)


class ResourceOutputValidator(object):

    def __init__(self, wrapper_context, initiator_handler):
        self.wrapper_context = wrapper_context
        self.initiator_handler = initiator_handler

    def validate_out(self, exp_resources_key_name):
        logger.info('validate_out')
        current_handler = self.initiator_handler
        while current_handler:
            current_handler.validate_resource(self.wrapper_context, exp_resources_key_name)
            current_handler = current_handler.next_handler


@pytest.fixture(scope="function")
def test_manager(sqs_mock, s3_mock, dynamodb_mock, sns_mock):
    logger.info('started')
    yield AWSResourceInitializer(sqs_mock, s3_mock, dynamodb_mock, sns_mock)
    logger.info('Waiting in test manager')


def test_moto_sqs_lambda(test_manager, sqs_mock):
    res_out_validator = test_manager.mock_env('src/test.yaml')

    sqs_mock.send_message(QueueUrl='bp.dip.demo.fifo',
                          MessageBody=json.dumps("Hi... Message had received successfully"))
    logger.info("Message has been sent")

    response = sqs_mock.receive_message(QueueUrl='bp.dip.demo.fifo')
    received_json = response["Messages"][0]["Body"]
    logger.info(received_json)
    res_out_validator.validate_out('validate_dc_event')



def test_moto_dynamodb_lambda(test_manager, dynamodb_mock):
    test_manager.mock_env('src/test.yaml')
    dynamodb_table = dynamodb_mock.Table('dynamodb_table_name')
    dynamodb_table.put_item(
        Item={
            'source_sys_name': 'ODP',
            'market': 'AU',
            'value': '20'
        }
    )
    logger.info("Item has successfully added to dynamodb table")

    response = dynamodb_table.get_item(
        Key={"source_sys_name": "ODP", 'market': 'AU'}
    )
    gxs_response = dynamodb_table.get_item(
        Key={"source_sys_name": "GXS", 'market': 'AU'}
    )
    logger.info("Successfully read item from dynamodb table")
