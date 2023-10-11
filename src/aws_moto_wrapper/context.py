import boto3
from aws_lambda_powertools import Logger

logger = Logger(child=True)


class TestEnvContext(object):
    sns_back_sqs_obj = {}
    _instance = None
    sns_name_to_resource_map = {}
    sqs_name_to_resource_map = {}

    #  Object
    def __new__(cls):
        raise NotImplemented('Class can not instantiated')

    @classmethod
    def set_sns_backed_sqs(cls, sns_name, sqs_res_obj):
        cls.sns_back_sqs_obj[sns_name] = sqs_res_obj

    @classmethod
    def get_sns_backed_sqs(cls, sns_name):
        return cls.sns_back_sqs_obj.get(sns_name, None)

    @classmethod
    def set_sns_resource(cls, sns_name, sns_resource_obj):
        cls.sns_name_to_resource_map[sns_name] = sns_resource_obj

    @classmethod
    def get_sns_resource(cls, sns_name):
        return cls.sns_name_to_resource_map.get(sns_name)

    @classmethod
    def set_sqs_resource(cls, sqs_name, sqs_resource_obj):
        cls.sqs_name_to_resource_map[sqs_name] = sqs_resource_obj

    @classmethod
    def get_sns_resource(cls, sqs_name):
        return cls.sqs_name_to_resource_map.get(sqs_name)
