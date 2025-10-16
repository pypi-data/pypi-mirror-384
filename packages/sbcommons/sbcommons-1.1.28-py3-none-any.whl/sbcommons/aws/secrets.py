import botocore
import botocore.session
from botocore.errorfactory import ClientError
from aws_secretsmanager_caching import SecretCache, SecretCacheConfig
from sbcommons.logging.lambda_logger import get_logger
from sbcommons.utils import evaluate_recursively

logger = get_logger("Sbcommnons Secrets")


def get_secret(secret_name: str, region_name: str = 'eu-north-1'):
    """ This function returns a cached secret stored in an AWS region

    AWS Secrets Manager enables you to replace hardcoded credentials in your code, including
    passwords, with an API call to Secrets Manager to retrieve the secret programmatically.
    This helps ensure the secret can't be compromised by someone examining your code,
    because the secret no longer exists in the code. This function returns the requested secret
    stored in AWS secret manager.
    When you retrieve a secret, you can use the Secrets Manager Python-based caching component
    to cache it for future use. Retrieving a cached secret is faster than retrieving it from
    Secrets Manager. Because there is a cost for calling Secrets Manager APIs,
    using a cache can reduce your costs.

    Args:
        secret_name (str) : The unique secret name stored in AWS secret manager
        region_name (str) : The AWS region. Default is eu-north-1

    Returns:
        A dict containing the secret. Example {"username":"ABC123"}. AWS returns a string, but we
        use a UDF to evaluate to string to the right python object.
    """
    try:
        client = botocore.session.get_session().create_client(service_name='secretsmanager',
                                                              region_name=region_name)
        cache_config = SecretCacheConfig()
        cache = SecretCache(config=cache_config, client=client)
        secret = cache.get_secret_string(secret_name)
        return evaluate_recursively(obj=secret, logger=logger)

    except ClientError as e:
        if e.response['Error']['Code'] == 'DecryptionFailureException':
            logger.error('Secrets Manager can''t decrypt the protected secret text using the '
                         'provided KMS key.')
            raise e
        elif e.response['Error']['Code'] == 'InternalServiceErrorException':
            logger.error('An error occurred on the server side.')
            raise e
        elif e.response['Error']['Code'] == 'InvalidParameterException':
            logger.error('You provided an invalid value for a parameter.')
            raise e
        elif e.response['Error']['Code'] == 'InvalidRequestException':
            logger.error('You provided a parameter value that is not valid for the current '
                         'state of the resource.')
            raise e
        elif e.response['Error']['Code'] == 'ResourceNotFoundException':
            logger.error('We can''t find the resource that you asked for.')
            raise e
        else:
            logger.error(f"Error:{e.response['Error']['Code']}")
            raise e
