from sbcommons.logging import lambda_logger
import requests

logger = lambda_logger.get_logger(__name__)


def post_to_webhook(service: str, webhook_url: str, json: dict) -> bool:
    try:
        response = requests.post(webhook_url, json=json)
        if not response.status_code == 200:
            logger.error(
                f'Tried to post message on {service} webhook but failed, status code: {response.status_code}'
            )
            return False
    except Exception as e:
        logger.error(f'Exception when posting to {service}, exception args: {e.args}')
        return False

    return True
