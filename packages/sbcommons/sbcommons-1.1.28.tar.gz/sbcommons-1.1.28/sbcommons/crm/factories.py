from typing import Dict
from typing import List
from typing import Union

from sbcommons.crm.symplify import SymplifyClient
from sbcommons.crm.symplify import SymplifyParser
from sbcommons.crm.klaviyo import KlaviyoClient
from sbcommons.crm.klaviyo import KlaviyoParser
from sbcommons.crm.parser import TranslationEntry


SUPPORTED_CRM_PLATFORMS = ['symplify', 'klaviyo']


class InvalidCrmPlatform(Exception):
    """ Invalid/Not supported Crm Platform class"""
    def __init__(self, msg):
        Exception.__init__(msg)


class ClientFactory:
    @classmethod
    def create_client(cls, crm_platform_name: str, token: Union[str, Dict[str, str]], **kwargs) \
            -> Union[SymplifyClient, KlaviyoClient]:
        """

        Args:
            crm_platform_name: The name of the CRM platform to create a client for. E.g. Symplify,
                Klaviyo.
            token: The access token to be used to instantiate the client.
            kwargs: Dictionary of keyword arguments that are passed to the client's constructor.

        Raises:
            InvalidCrmPlatform if the crm_platform_name parameter is not one of the values in
                SUPPORTED_CRM_PLATFORMS.
        """
        if crm_platform_name == 'symplify':
            client_class = SymplifyClient
        elif crm_platform_name == 'klaviyo':
            client_class = KlaviyoClient
        else:
            raise InvalidCrmPlatform(f'CRM platform {crm_platform_name} is not supported. Select '
                                     f'one of {SUPPORTED_CRM_PLATFORMS}')
        return client_class(token=token, **kwargs)


class ParserFactory:
    @classmethod
    def create_parser(cls, crm_platform_name: str, translation_entries: List[TranslationEntry],
                      **kwargs) -> Union[SymplifyParser, KlaviyoParser]:
        """

        Args:
            crm_platform_name: The name of the CRM platform to create a client for. E.g. Symplify,
                Klaviyo.
            translation_entries: A list of translation entry objects used to parse the results
                    of the SQL query to the format required by the CRM tool.

        Raises:
            InvalidCrmPlatform if the crm_platform_name parameter is not one of the values in
                SUPPORTED_CRM_PLATFORMS.
        """
        if crm_platform_name == 'symplify':
            parser_class = SymplifyParser
        elif crm_platform_name == 'klaviyo':
            parser_class = KlaviyoParser
        else:
            raise InvalidCrmPlatform(f'CRM platform {crm_platform_name} is not supported. Select '
                                     f'one of {SUPPORTED_CRM_PLATFORMS}')
        return parser_class(translation_entries=translation_entries, **kwargs)
