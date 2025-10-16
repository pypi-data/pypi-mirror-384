from abc import ABC, abstractmethod
import logging
import requests
from requests.adapters import HTTPAdapter
from requests.structures import CaseInsensitiveDict
from time import sleep
from typing import Dict
from typing import Union
from urllib3 import Retry
from urllib.error import HTTPError
from sbcommons.utils import remove_email_info_from_text


class CrmClient(ABC):
    """ Base class for clients used to connect to CRM tools.

    Attributes:
        token (str, Dict[str, str]): Token needed to access the CRM's API. This is either a single
            API key or a Dict with two keys, the PUBLIC_API_KEY and PRIVATE_API_KEY.
        session (requests.Session): The session object for the Symplify connection.
        rate_limit (int): Amounts of second to wait after getting a rate limited error (HTTP 429),
            in order to make a successful request again.
        max_rate_limit_retries (int): Number of times to retry making a request if a rate limited
            error occurs (status code 429/Too Many Requests).
    """

    def __init__(self, token: Union[str, Dict[str, str]], rate_limit: int,
                 max_rate_limit_retries: int):
        assert rate_limit > 0
        assert max_rate_limit_retries > 0
        self.token = token
        self.max_rate_limit_retries = max_rate_limit_retries
        self.rate_limit = rate_limit
        self.session = requests.session()

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, excl_value, exc_traceback):
        self.session.__exit__()

    @abstractmethod
    def connect(self):
        raise NotImplementedError("connect method should be implemented by children "
                                  "classes of CrmClient.")

    @abstractmethod
    def _build_base_header(self) -> CaseInsensitiveDict:
        """ Method that should return the session header content as a dictionary. """
        raise NotImplementedError("_build_base_header method should be implemented by children "
                                  "classes of CrmClient.")

    @property
    @abstractmethod
    def logger(self) -> logging.Logger:
        """ Returns the logger object to be used by the instance. This must be implemented by
            child classes, using a distinct logger name corresponding to the child class. """
        raise NotImplementedError("Classes inheriting from CrmClient should implement the "
                                  "logger method with a @property decorator.")

    @staticmethod
    def _retry_adapter(retries=5,
                       backoff_factor=1.0,
                       status_forcelist=(500, 501, 502, 503, 504)):
        retry = Retry(
            total=retries,
            read=retries,
            connect=retries,
            backoff_factor=backoff_factor,
            status_forcelist=status_forcelist,
        )
        return HTTPAdapter(max_retries=retry)

    def _request(self, method: str = 'GET', url: str = None, verbose: bool = False, *args,
                 **kwargs) -> requests.Response:
        """ Helper/Wrapper method around the sessions.request API.

        Args:
            method: The type of request.
            url: The url to use for the request.
            verbose: Whether to write out the response of the call as text with the logger.

        Returns:
            A requests.Response object corresponding to the request's response.

        Raises:
            HTTPError if the response status codeis different than 200 and 429, or if it is 429 but
                all attempts to retry the request fail.
        """
        for i in range(self.max_rate_limit_retries):
            response = self.session.request(method, url, *args, **kwargs)

            # Continue the loop only if we got a rate limit error
            if response.status_code != 429:
                break

            # Rate limited error (we should make one request per minute).
            self.logger.warning(
                f'Rate limited by the CRM server API. Sleeping for {self.rate_limit} seconds'
            )
            # Wait and re-try the request
            sleep(self.rate_limit)

        # If an error occurred during the request, raise an exception
        if response.status_code not in [200,201,202]:
            response_content_clean = remove_email_info_from_text(str(response.content))
            e_msg = f'HTTP response code: {response.status_code} - Response reason: ' \
                f'{response.reason} and content {response_content_clean}'
            self.logger.error(e_msg)
            raise HTTPError(url, response.status_code, e_msg, None, None)

        if verbose:
            self.logger.info(f"Response text: {response.text}")
        return response

    def post_list_sync(self, list_data: Union[bytes, Dict], import_type: str = 'ADD') -> bool:
        """ Posts a list of customers to the CRM tool - synchronous call."""
        raise NotImplementedError(f'post_list_sync has not been implemented in {self.__class__}')

    def post_survey_candidates(self, **kwargs):
        """ Wrapper around post_list_sync. Used to achieve polymorphism with other CrmClient
        subclasses such as KlaviyoClient. We do this because we might use different methods to post
        survey candidates in different CRM systems. """
        return self.post_list_sync(**kwargs)
