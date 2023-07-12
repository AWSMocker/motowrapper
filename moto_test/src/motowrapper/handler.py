import abc
from abc import ABC, abstractmethod

import io

from dataclasses import dataclass

import logging


@dataclass
class WrapperContext(object):
    sqs = None
    s3 = None
    env_in_json = None

    def __init__(self, sqs, s3, env_in_json):
        self.sqs = sqs
        self.s3 = s3
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


sqs_handler = SQSHandler(None)
s3_handler = S3Handler(sqs_handler)
env_creator = EnvCreator(s3_handler)
