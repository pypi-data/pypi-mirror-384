import logging
import requests
from requests.structures import CaseInsensitiveDict
from time import sleep


from sbcommons.crm.client import CrmClient


class SymplifyClient(CrmClient):
    """ A client class to interact with Symplify's API.

    Attributes:
        token (str): Token needed to access Symplify's API. Inherited from CrmClient.
        customer_id (str): Customer here refers to our company. This id corresponds to our company
            account on Symplify.
        list_id (int): Identifier of the list to use for pushing/retrieving customers.
        delimiter (str): Delimiter to use to separate column fields in exports.
        session (requests.Session): The session object for the Symplify connection. Inherited from
            CrmClient.
        rate_limit (int): Amounts of second to wait after getting a rate limited error (HTTP 429),
            in order to make a successful request again. Inherited from CrmClient.
        max_rate_limit_retries (int): Number of times to retry making a request if a rate limited
            error occurs (status code 429/Too Many Requests). Inherited from CrmClient.
    """

    # Symplify's REST API base URL
    BASE_URL = 'http://www.carmamail.com:80/rest/'

    def __init__(self, token: str, customer_id: str, list_id: int = None, delimiter: str = '|',
                 rate_limit=60, max_rate_limit_retries=2, logger: logging.Logger = None):
        CrmClient.__init__(self, token=token, rate_limit=rate_limit,
                           max_rate_limit_retries=max_rate_limit_retries)
        self.customer_id = customer_id
        self.list_id = list_id
        self.delimiter = delimiter
        # If logger argument is None, use default logger
        self._logger = logger or logging.getLogger(__name__)

    @property
    def logger(self) -> logging.Logger:
        """ Returns the logger object to be used by the instance. """
        return self._logger

    def connect(self):
        """ Performs the necessary actions required to be able to make requests to Symplify.

        This method is automatically called when this class is used in a context manager i.e. when
        __enter__ is called.
        """
        self.session.mount('https://', self._retry_adapter(retries=3, backoff_factor=4))
        self.session.headers = self._build_base_header()

    def close(self):
        """ Performs necessart actions to terminate the connection with Symplify. """
        self.session.close()

    def _build_base_header(self) -> CaseInsensitiveDict:
        """ Builds a dictionary that includes the header's basic elements for making requests. """
        return CaseInsensitiveDict({
            'Accept': 'application/json',
            'X-Carma-Authentication-Token': self.token
        })

    def _build_url(self, endpoint: str) -> str:
        """ Builds the URL that will be used for requests to the Symplify API.

        Args:
            endpoint: The part of the request URL following <server>/rest/<customerId>.

        Returns:
            A string representing the URL.
        """
        return f'{self.BASE_URL}{self.customer_id}/{endpoint}'

    def create_import(self, import_type: str = 'ADD', identity_column: str = 'originalId') -> str:
        """ Calls the Symplify API to create an id for importing customers into the list.

        Args:
            import_type: This can be either 'ADD' or 'REPLACE'. Using 'ADD' will add new customers
                to the list, updating the attributes of those that already exist. 'REPLACE' will
                delete all customers from the list and replace them with the new ones.
            identity_column: The name of the column in the imported data that is used to distinguish
                between customers. If we import a customer with an originalId that already exists in
                the list and we use the 'ADD' import type, then we will simply update the attributes
                of that customer.

        Returns:
            The identifier to use for importing into the list.
        """
        url = self._build_url(f'lists/{self.list_id}/imports')
        payload = {
            'delimiter': f'{ord(self.delimiter)}',
            'encoding': 'UTF8',
            'type': import_type,
            'identityColumn': identity_column
        }
        return self._request(method='POST', url=url, json=payload, verbose=True).json()['id']

    def post_list_async(self, import_type: str, list_data: bytes) -> int:
        """ Posts a list of customers to Symplify - asynchronous call.

            import_type: This can be either 'ADD' or 'REPLACE'. Using 'ADD' will add new customers
                to the list, updating the attributes of those that already exist. 'REPLACE' will
                delete all customers from the list and replace them with the new ones.
            identity_column: The name of the column in the imported data that is used to distinguish
                between customers. If we import a customer with an originalId that already exists in
                the list and we use the 'ADD' import type, then we will simply update the attributes
                of that customer.

            Returns:
                The batch id for the batch import job. The batch id can be used to track the
                    asynchronous call and get its status using the <check_batch_status> method.
        """
        import_id = self.create_import(import_type=import_type)
        url = self._build_url(endpoint=f'lists/{self.list_id}/recipients/{import_id}')
        self.session.headers['Content-Type'] = 'text/csv'
        return self._request(method='POST', url=url, data=list_data, verbose=True).json()['batchId']

    def post_list_sync(self, list_data: bytes, import_type: str = 'ADD') -> bool:
        """ Posts a list of customers to Symplify - synchronous call.

            import_type: This can be either 'ADD' or 'REPLACE'. Using 'ADD' will add new customers
                to the list, updating the attributes of those that already exist. 'REPLACE' will
                delete all customers from the list and replace them with the new ones.
            identity_column: The name of the column in the imported data that is used to distinguish
                between customers. If we import a customer with an originalId that already exists in
                the list and we use the 'ADD' import type, then we will simply update the attributes
                of that customer.

            Returns:
                True if the job succeeded. False otherwise.
        """
        batch_id = self.post_list_async(import_type=import_type, list_data=list_data)
        symplify_batch_status = self.check_batch_status(batch_id)
        while symplify_batch_status != 'FINISHED' and symplify_batch_status != 'ERROR':
            sleep(self.rate_limit)
            symplify_batch_status = self.check_batch_status(batch_id)
        job_succeeded = True if symplify_batch_status == 'FINISHED' else False
        return job_succeeded

    def check_batch_status(self, batch_id: int):
        url = self._build_url(endpoint=f'batches/{batch_id}')
        self.session.headers['Content-Type'] = 'application/json'
        return self._request(method='GET', url=url, verbose=True).json()['status']

    def clean_list(self) -> bool:
        """ Clears all customer data from a list.

        Returns:
            True if the list was successfully cleaned. False otherwise.
        """
        payload_type = 'REPLACE'
        header = 'originalId'
        str_data = f'{header}'

        self.logger.info(f'Posting 0 rows to list {self.list_id}.')
        bytes_data = str_data.encode('utf-8')
        job_succeeded = self.post_list_sync(import_type=payload_type, list_data=bytes_data)
        return job_succeeded

    def post_survey_candidates(self, **kwargs):
        """ Wrapper around post_list_sync. Used to achieve polymorphism with other CrmClient
        subclasses such as KlaviyoClient. We might use different methods to post survey candidates
        in different CRM systems. """
        return self.post_list_sync(**kwargs)
