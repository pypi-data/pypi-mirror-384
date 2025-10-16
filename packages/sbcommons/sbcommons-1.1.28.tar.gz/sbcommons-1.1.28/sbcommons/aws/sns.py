import functools
import traceback
from typing import Any

import boto3


def sns_client(region: str) -> Any:
    return boto3.client('sns', region_name=region)


def publish(topic_arn: str, region: str, message: str):
    client = sns_client(region)
    client.publish(
        TargetArn=topic_arn,
        Message=message
    )


def publish_to_sns_on_failure(topic_arn: str, region: str = 'eu-north-1'):
    """ Parametrizes a decorator function for publishing to an SNS topic on failure.

    If an exception is raised by the function we use the decorator on, the exception stack traceback
    is pushed as a message to the SNS topic defined by <topic_arn> and <region>. Then the caught
    exception is re-raised.

    Example use with lambda function:
        @publish_to_sns_on_failure(<arn_topic>, 'eu-north-1')
        def handler(event, context):
            ...
            <code that can raise an exception>
            ...
            return {'statusCode': 200}
            
    Args:
        topic_arn: AWS SNS topic to publish a message to.
        region: The AWS region of the SNS topic.
        
    Return:
        The actual decorator function for publishing to a specific SNS topic.
    """
    def actual_decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                exc_traceback = traceback.format_exc()
                publish(topic_arn=topic_arn, region=region, message=exc_traceback)
                raise e
        return wrapper
    return actual_decorator
