import abc
from abc import ABC, abstractmethod

import io

from dataclasses import dataclass

import logging

from aws_lambda_powertools import Logger

from .context import TestEnvContext


@dataclass
class MotoWrapperContext(object):
    sqs = None
    s3 = None
    sns = None
    dynamodb = None
    env_in_json = None

    def __init__(self, sqs, s3, dynamodb, sns, env_in_json, test_name_to_exp_res,global_config):
        self.sqs = sqs
        self.s3 = s3
        self.dynamodb = dynamodb
        self.env_in_json = env_in_json
        self.sns = sns
        self.test_name_to_exp_res = test_name_to_exp_res
        self.global_config = global_config



class AbstractServiceHandler(ABC):
    next_handler = None

    def __init__(self, next_handler):
        self.next_handler = next_handler
        pass

    def prepare_env(self, wrapper_context: MotoWrapperContext):
        pass

    def validate_resource(self, wrapper_context: MotoWrapperContext, exp_resources_key_name:str):
        pass


class S3ServiceHandler(AbstractServiceHandler):
    S3_SERVICE_KEY = 'S3'
    S3_BUCKET_NAME = 'bucketName'
    S3_FILES = 'files'

    def __init__(self, next_handler):
        super().__init__(next_handler)

    def prepare_env(self, wrapper_context: MotoWrapperContext):
        s3_envs = wrapper_context.env_in_json[S3ServiceHandler.S3_SERVICE_KEY]
        for env in s3_envs:
            bucket_name = env.get(S3ServiceHandler.S3_BUCKET_NAME)

            wrapper_context.s3.create_bucket(
                Bucket=bucket_name
            )
            logging.info('Bucket created ')
            files = env.get(S3ServiceHandler.S3_FILES)
            for file in files:
                _from_local_to_s3(wrapper_context.s3, bucket_name, file.get('s3FileName'),
                                  file.get('localFile'))
        print("s3 handler")

    def validate_resource(self, moto_wrapper_context: MotoWrapperContext, exp_resources_key_name:str):
        s3_envs = moto_wrapper_context.test_name_to_exp_res[exp_resources_key_name]\
                        .get(S3ServiceHandler.S3_SERVICE_KEY, [])
        for env in s3_envs:
            print(env)
        print("s3 handler")


class SQSServiceHandler(AbstractServiceHandler):
    SQS_SERVICE_KEY = 'SQS'
    SQS_NAME = 'Name'

    def _get_service_tag(self):
        return 'SQS'

    def __init__(self, next_handler):
        super().__init__(next_handler)

    def prepare_env(self, wrapper_context: MotoWrapperContext):
        sqs_envs = wrapper_context.env_in_json[SQSServiceHandler.SQS_SERVICE_KEY]
        for env in sqs_envs:
            sqs_name = env.get(SQSServiceHandler.SQS_NAME)

            wrapper_context.sqs.create_queue(
                QueueName=sqs_name
            )
            logging.info('SQS created ')
        print('SQS Handler')
    def validate_resource(self, moto_wrapper_context: MotoWrapperContext, exp_resources_key_name:str):
        sqs_envs = moto_wrapper_context.test_name_to_exp_res[exp_resources_key_name]\
                                        .get(SQSServiceHandler.SQS_SERVICE_KEY, [])
        for env in sqs_envs:
            print(env)
        print("sqs_envs handler")

class DynamodbServiceHandler(AbstractServiceHandler):
    DYNAMODB_SERVICE_KEY = 'DynamoDB'
    TABLE_NAME = 'Name'
    KEY_SCHEMA_NAME = 'KeySchema'
    ATTRIBUTE_DEFINITION_NAME = 'AttributeDefinitions'
    GLOBAL_SECONDARY_INDEX_PROP_NAME = 'GlobalSecondaryIndexes'
    INITIAL_LOAD_PROP_NAME = 'InitialLoad'

    def __init__(self, next_handler):
        super().__init__(next_handler)

    def prepare_env(self, wrapper_context: MotoWrapperContext):
        dynamodb_envs = wrapper_context.env_in_json[DynamodbServiceHandler.DYNAMODB_SERVICE_KEY]
        for env in dynamodb_envs:
            table_name = env.get(DynamodbServiceHandler.TABLE_NAME)
            key_schema_name = env.get(DynamodbServiceHandler.KEY_SCHEMA_NAME)
            attribute_definiton_name = env.get(DynamodbServiceHandler.ATTRIBUTE_DEFINITION_NAME)
            global_secondary_index = env.get(DynamodbServiceHandler.GLOBAL_SECONDARY_INDEX_PROP_NAME)
            wrapper_context.dynamodb.create_table(
                TableName=table_name,
                KeySchema=key_schema_name,  # _generate_key_schema(key_schema_name),
                GlobalSecondaryIndexes=global_secondary_index,
                AttributeDefinitions=attribute_definiton_name
                # _generate_attribute_definition(attribute_definiton_name)
            )
            logging.info('DynamoDB Table has been created ')
            files = env.get(DynamodbServiceHandler.INITIAL_LOAD_PROP_NAME)
            for file in files:
                _from_local_to_dynamodb(wrapper_context.dynamodb, table_name,
                                        file.get('SourceType'), file.get('localFile'))
        print('Dyanmodb Handler')

    def validate_resource(self, moto_wrapper_context: MotoWrapperContext, exp_resources_key_name:str):
        dynamodb_env = moto_wrapper_context.test_name_to_exp_res[exp_resources_key_name]\
                                        .get(DynamodbServiceHandler.DYNAMODB_SERVICE_KEY, [])
        for env in dynamodb_env:
            print(env)
        print("dynamodb_env handler")

class EnvCreator(object):

    def __init__(self, initiator_handler: AbstractServiceHandler):
        self.initiator_handler = initiator_handler

    def prepare_env(self, wrapper_context: MotoWrapperContext):
        current_handler = self.initiator_handler
        while current_handler:
            current_handler.prepare_env(wrapper_context)
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


def _from_local_to_dynamodb(dynamodb, table_name, source_type,
                            file_loc, encoding='utf-8'):
    table = dynamodb.Table(table_name)
    with io.open(file_loc, "r", encoding=encoding) as data_file:
        column_names = next(data_file).strip("\n").split(',')
        for records in data_file:
            record = records.strip("\n").split(',')
            item = {}
            for idx, column_name in enumerate(column_names):
                item[column_name.lower()] = record[idx]
            table.put_item(
                Item=item
            )
    logger.info("Successfully inserted initial load to dynamodb table")


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


logger = Logger(child=True)


class SNSServiceHandler(AbstractServiceHandler):
    SNS_SERVICE_KEY = 'SNS'
    SNS_NAME_PROP_KEY = 'Name'

    def _get_service_tag(self):
        return 'SQS'

    def __init__(self, next_handler):
        super().__init__(next_handler)

    def prepare_env(self, wrapper_context: MotoWrapperContext):
        sns_envs = wrapper_context.env_in_json[SNSServiceHandler.SNS_SERVICE_KEY]
        for env in sns_envs:
            sns_name = env.get(SNSServiceHandler.SNS_NAME_PROP_KEY)

            # create fifo sns topic using boto3
            is_fifo = sns_name.lower().endswith('.fifo')
            sns_attributes = {"FifoTopic": str(is_fifo)}
            sns_obj = wrapper_context.sns.create_topic(
                Name=sns_name,
                Attributes=sns_attributes

            )

            TestEnvContext.set_sns_resource(sns_name=sns_name, sns_resource_obj=sns_obj)

            # create sqs queue and scubscribe to sns
            sqs_name = ''.join([sns_name.split('.')[0], '_queue', '.fifo']) if is_fifo else \
                ''.join([sns_name, '_queue'])
            sqs_attributes = {"FifoTopic": str(is_fifo)}
            sqs_obj = wrapper_context.sqs.create_queue(QueueName=sqs_name, Attributes=sqs_attributes)
            sqs_arn = wrapper_context.sqs.get_queue_attributes(QueueUrl=sqs_obj['QueueUrl'],
                                                               AttributeNames=['QueueArn'])
            wrapper_context.sns.subscribe(
                TopicArn=sns_obj['TopicArn'],
                Protocol='sqs',
                Endpoint=sqs_arn['Attributes']['QueueArn']
            )
            TestEnvContext.set_sns_backed_sqs(sns_name=sns_name, sqs_res_obj=sqs_obj)

            logger.info('SNS created ')
        logger.info('SNS Handler')

    def validate_resource(self, moto_wrapper_context: MotoWrapperContext, exp_resources_key_name:str):
        sns_env = moto_wrapper_context.test_name_to_exp_res[exp_resources_key_name]\
                                        .get(SNSServiceHandler.SNS_SERVICE_KEY, [])
        for env in sns_env:
            print(env)
        print("sns_env handler")


sqs_handler = SQSServiceHandler(None)
s3_handler = S3ServiceHandler(sqs_handler)
dynamodb_handler = DynamodbServiceHandler(s3_handler)
sns_handler = SNSServiceHandler(dynamodb_handler)
env_creator = EnvCreator(sns_handler)
