import abc
from abc import ABC, abstractmethod

import io

from dataclasses import dataclass

import logging


@dataclass
class WrapperContext(object):
    sqs = None
    s3 = None
    dynamodb = None
    env_in_json = None

    def __init__(self, sqs, s3, dynamodb, env_in_json):
        self.sqs = sqs
        self.s3 = s3
        self.dynamodb = dynamodb
        self.env_in_json = env_in_json


class AbstractHandler(ABC):
    next_handler = None

    def __init__(self, next_handler):
        self.next_handler = next_handler
        pass

    def prepare(self, wrapper_context: WrapperContext):
        self.handler(wrapper_context)

    @abstractmethod
    def handler(self, wrapper_context: WrapperContext):
        pass


class S3Handler(AbstractHandler):
    S3_SERVICE_KEY = 'S3'
    S3_BUCKET_NAME = 'bucketName'
    S3_FILES = 'files'

    def __init__(self, next_handler):
        super().__init__(next_handler)

    def handler(self, wrapper_context: WrapperContext):
        s3_envs = wrapper_context.env_in_json[S3Handler.S3_SERVICE_KEY]
        for env in s3_envs:
            bucket_name = env.get(S3Handler.S3_BUCKET_NAME)

            wrapper_context.s3.create_bucket(
                Bucket=bucket_name
            )
            logging.info('Bucket created ')
            files = env.get(S3Handler.S3_FILES)
            for file in files:
                _from_local_to_s3(wrapper_context.s3, bucket_name, file.get('s3FileName'),
                                  file.get('localFile'))
        print("s3 handler")

class SQSHandler(AbstractHandler):
    SQS_SERVICE_KEY = 'SQS'
    SQS_NAME = 'Name'
    def _get_service_tag(self):
        return 'SQS'

    def __init__(self, next_handler):
        super().__init__(next_handler)

    def handler(self, wrapper_context: WrapperContext):
        sqs_envs = wrapper_context.env_in_json[SQSHandler.SQS_SERVICE_KEY]
        for env in sqs_envs:
            sqs_name = env.get(SQSHandler.SQS_NAME)

            wrapper_context.sqs.create_queue(
                QueueName=sqs_name
            )
            logging.info('SQS created ')
        print('SQS Handler')


class DynamodbHandler(AbstractHandler):
    DYNAMODB_SERVICE_KEY = 'DynamoDB'
    TABLE_NAME = 'Name'
    KEY_SCHEMA_NAME = 'KeySchema'
    ATTRIBUTE_DEFINITION_NAME = 'AttributeDefinitions'

    def __init__(self, next_handler):
        super().__init__(next_handler)

    def handler(self, wrapper_context: WrapperContext):
        dynamodb_envs = wrapper_context.env_in_json[DynamodbHandler.DYNAMODB_SERVICE_KEY]
        for env in dynamodb_envs:
            table_name = env.get(DynamodbHandler.TABLE_NAME)
            key_schema_name = env.get(DynamodbHandler.KEY_SCHEMA_NAME)
            attribute_definiton_name = env.get(DynamodbHandler.ATTRIBUTE_DEFINITION_NAME)
            wrapper_context.dynamodb.create_table(
                TableName=table_name,
                KeySchema= _generate_key_schema(key_schema_name),
                AttributeDefinitions = _generate_attribute_definition(attribute_definiton_name)
            )
            logging.info('DynamoDB Table has been created ')
        print('Dyanmodb Handler')

class EnvCreator(object):

    def __init__(self, initiator_handler: AbstractHandler):
        self.initiator_handler = initiator_handler

    def prepare_env(self, wrapper_context: WrapperContext):
        current_handler = self.initiator_handler
        while current_handler:
            current_handler.prepare(wrapper_context)
            current_handler = current_handler.next_handler



def _from_local_to_s3(s3, bucket_name, key_name,
                      file_loc, encoding='utf-8'):
    with io.open(file_loc, "r", encoding=encoding) as read_file:
        data_file = read_file.read()
        s3.put_object(
            Body=data_file,
            Bucket=bucket_name,
            Key=key_name
        )

def _generate_key_schema(key_schema_name):
    key_schema = []
    for itr in key_schema_name:
        schema = {}
        schema['AttributeName'] = itr.get('AttributeName')
        schema['KeyType'] = itr.get('KeyType')
        key_schema.append(schema)
    return key_schema

def _generate_attribute_definition(attribute_definiton_name):
    attr_definition = []
    for itr in attribute_definiton_name:
        definition = {}
        definition['AttributeName'] = itr.get('AttributeName')
        definition['AttributeType'] = itr.get('AttributeType')
        attr_definition.append(definition)
    return attr_definition

sqs_handler = SQSHandler(None)
s3_handler = S3Handler(sqs_handler)
dynamodb_handler = DynamodbHandler(s3_handler)
env_creator = EnvCreator(dynamodb_handler)
