# from moto_test.src.motowrapper.context import TestEnvContext
# from moto_test.src.motowrapper.wrapper import AWSResourceInitializer
import pytest

from aws_lambda_powertools.logging import Logger

from src.aws_moto_wrapper.context import TestEnvContext
from src.aws_moto_wrapper.wrapper import AWSResourceInitializer
import io

logger = Logger()


def test_moto_s3_mock_single_file(test_manager, s3_mock):
    res_out_validator = test_manager.mock_env('test/input/test_s3/test_s3.yaml')
    objects = s3_mock.list_objects_v2(Bucket='dip-single-file-bucket')
    contents = objects.get('Contents', [])
    assert len(contents) == 1

    __validate_s3_file_to_local(s3_mock, 'dip-single-file-bucket', 'mock/input/lookup.csv', 'test/input/lookup.csv')


#
def test_moto_s3_mock_multi_file(test_manager, s3_mock):
    res_out_validator = test_manager.mock_env('test/input/test_s3/test_s3.yaml')
    objects = s3_mock.list_objects_v2(Bucket='dip-sfg-integration-bucket')
    contents = objects.get('Contents', [])
    assert len(contents) == 2

    __validate_s3_file_to_local(s3_mock, 'dip-sfg-integration-bucket',
                                'inbound/producteso-au/site_lookup.json', 'test/input/site_lookup.json')

    __validate_s3_file_to_local(s3_mock, 'dip-sfg-integration-bucket',
                                'inbound/producteso-au/product_config.xml', 'test/input/product_config.xml')


def __validate_s3_file_to_local(s3_mock, bucket, s3_key, local_file_loc):
    s3_data = s3_mock.get_object(
        Bucket=bucket,
        Key=s3_key
    )
    data = s3_data["Body"].read().decode("utf-8")
    with io.open(local_file_loc, "r", encoding='utf-8') as read_file:
        data_file = read_file.read()
    assert data_file == data


def test_moto_s3_validate_single_file(test_manager, s3_mock):
    res_out_validator = test_manager.mock_env('test/input/test_s3/test_s3.yaml')
    objects = s3_mock.list_objects_v2(Bucket='dip-single-file-bucket')
    contents = objects.get('Contents', [])

    res_out_validator.validate_out('single_file')

def test_moto_s3_validate_multi_file(test_manager, s3_mock):
    res_out_validator = test_manager.mock_env('test/input/test_s3/test_s3.yaml')
    objects = s3_mock.list_objects_v2(Bucket='dip-single-file-bucket')
    contents = objects.get('Contents', [])

    res_out_validator.validate_out('multiple_file')