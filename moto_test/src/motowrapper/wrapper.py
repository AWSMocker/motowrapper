from dataclasses import dataclass

import yaml
import json
import boto3
import pytest
from functools import partial

from dacite import from_dict
from moto import mock_s3
from yaml.loader import SafeLoader
from moto import mock_sns, mock_sqs
from dataclasses import dataclass, field
from moto_test.src.motowrapper.handler import env_creator, WrapperContext


# Open the file and load the file
def __convert_to_json(file_location):
    with open(file_location) as f:
        return yaml.load(f, Loader=SafeLoader)


def __mock_env(sqs, s3, env_detail, file_type='yaml'):
    json_stack = __jsonfy_evn_details(env_detail, file_type)

    setup_list = json_stack.get("setup")

    env_creator.prepare_env(WrapperContext(sqs=sqs, s3=s3, env_in_json=setup_list))
    s3.create_bucket(
        Bucket='Bucket'
    )
    print('__create_json_dict down')
    return "json_stack"


def __jsonfy_evn_details(env_detail, file_type):
    if file_type.lower() == "yaml":
        json_stack = __convert_to_json(env_detail)
    else:
        with open(env_detail) as f:
            json_stack = json.load(f)
    return json_stack


@pytest.fixture(scope="module")
def moto_wrapper(mock_sqs, mock_s3):
    print('moto_wrapper')
    return partial(__mock_env, mock_sqs, mock_s3)


def test_moto_lambda(moto_wrapper, mock_s3):
    moto_wrapper('test.yaml')
    mock_s3.put_object(
        Body='This is daya',
        Bucket='Bucket',
        Key='/tmp/data/abc.txt'
    )
    file_content = mock_s3.get_object(Bucket='Bucket', Key='/tmp/data/abc.txt')

    file_content = file_content["Body"].read().decode("utf-8")
    print("Test", file_content)


@pytest.fixture(scope="module")
def moto_wrapper(sqs_mock, s3_mock):
    print('moto_wrapper')
    return partial(__mock_env, sqs_mock, s3_mock)


@pytest.fixture(scope="module")
def s3_mock():
    with mock_s3():
        print("\n S3 Up....")
        yield boto3.client("s3")
        print("\n S3 Down....")


@pytest.fixture(scope="module")
def sqs_mock():
    with mock_sqs():
        print("\n SQS Up....")
        yield boto3.client("sqs")
        print("\n SQS Down....")


def test_moto_lambda(moto_wrapper, s3_mock):
    moto_wrapper('moto_test/test.yaml')
    s3_mock.put_object(
        Body='This is daya',
        Bucket='Bucket',
        Key='/tmp/data/abc.txt'
    )
    file_content = s3_mock.get_object(Bucket='Bucket', Key='/tmp/data/abc.txt')

    file_content = file_content["Body"].read().decode("utf-8")
    print("Test", file_content)

def test_moto_sqs_lambda(moto_wrapper, sqs_mock):
    moto_wrapper('moto_test/test.yaml')
    sqs_mock.send_message(QueueUrl = 'bp.dip.demo.fifo',
            MessageBody = json.dumps("Hi... Message had received successfully"))
    print("Message has been sent")

    response = sqs_mock.receive_message(QueueUrl='bp.dip.demo.fifo')
    received_json = response["Messages"][0]["Body"]
    print(received_json)

