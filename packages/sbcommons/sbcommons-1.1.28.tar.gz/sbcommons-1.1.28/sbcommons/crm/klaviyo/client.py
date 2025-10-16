import json
import logging
import time
from typing import Dict, Callable, Any
from typing import List, Tuple
import requests
import urllib.parse

from requests.structures import CaseInsensitiveDict

from sbcommons.crm.klaviyo.url import (get_next_page_cursor_arg,
                                       get_filter_url,
                                       get_url_since_timestamp_filter_args,
                                       get_url_until_timestamp_filter_args,
                                       get_field_arg)
from sbcommons.utils import get_field_from_included, get_value_from_path, chunk_list
from sbcommons.crm.client import CrmClient
from sbcommons.crm.klaviyo.metric import KlaviyoMetric
from sbcommons.crm.klaviyo.metric import KlaviyoMetricError
from string import Template


class KlaviyoClientError(Exception):
    """ Klaviyo client exception class"""

    def __init__(self, msg):
        super(KlaviyoClientError, self).__init__(msg)


class KlaviyoClient(CrmClient):
    """ A client class to interact with Klaviyo's API.

    Attributes:
        token (Dict[str, str]): A Dict with two keys, the PUBLIC_API_KEY and PRIVATE_API_KEY
            required to make requests to Klaviyo. Inherited from CrmClient.
        list_id (int): Identifier of the list to use for pushing/retrieving customers.
        session (requests.Session): The session object for the Klaviyo connection. Inherited from
            CrmClient.
        rate_limit (int): Amounts of second to wait after getting a rate limited error (HTTP 429),
            in order to make a successful request again. Inherited from CrmClient.
        max_rate_limit_retries (int): Number of times to retry making a request if a rate limited
            error occurs (status code 429/Too Many Requests). Inherited from CrmClient.
    """

    _KLAVIYO_IDENTIFY_URL = 'https://a.klaviyo.com/client/profiles/?company_id='
    _KLAVIYO_UNSUBSCRIBE_URL = 'https://a.klaviyo.com/api/v1/people/exclusions'
    _KLAVIYO_TRACK_URL = 'https://a.klaviyo.com/client/events/?company_id='

    _KLAVIYO_GET_GROUP_MEMBERS_URL_TEMPLATE = ('https://a.klaviyo.com/api/lists/'
                                               '{list_id}/profiles/?fields[profile]=email&'
                                               'page[size]=100')
    _KLAVIYO_GET_SEGMENT_MEMBERS_URL_TEMPLATE = ('https://a.klaviyo.com/api/segments/{segment_id}'
                                                 '/profiles/?page[size]=100')
    _KLAVIYO_LIST_MEMBERS_URL = Template('https://a.klaviyo.com/api/lists/$id/relationships/'
                                         'profiles/?fields[profile]=email&page[size]=100')
    _KLAVIYO_SUBSCRIBE_PROFILES = 'https://a.klaviyo.com/api/profile-subscription-bulk-create-jobs/'
    _KLAVIYO_UPDATE_PROFILE_URL = 'https://a.klaviyo.com/api/profile-import/'
    _KLAVIYO_REQUEST_PROFILE_DELETION_URL = 'https://a.klaviyo.com/api/data-privacy-deletion-jobs/'
    _KLAVIYO_FLOWS_URL = "https://a.klaviyo.com/api/flows/?page[size]=50"
    _KLAVIYO_BULK_UPSERT_PROFILES_URL = 'https://a.klaviyo.com/api/profile-bulk-import-jobs/'
    _KLAVIYO_LIST_MEMBERS_COUNT = ('https://a.klaviyo.com/api/lists/id?additional-fields[list]'
                                   '=profile_count')
    _KLAVIYO_SEGMENT_MEMBERS_COUNT = ('https://a.klaviyo.com/api/segments/'
                                      'id?additional-fields[segment]=profile_count')
    _KLAVIYO_BULK_CREATE_EVENTS = 'https://a.klaviyo.com/api/event-bulk-create-jobs'
    _KLAVIYO_CAMPAIGNS_URL = "https://a.klaviyo.com/api/campaigns"
    EXCLUSION_REASONS = [
        'unsubscribed', 'bounced', 'invalid_email', 'reported_spam', 'manually_excluded'
    ]

    def __init__(self, token: Dict[str, str], list_id: str = None, segment_id=None, rate_limit=60,
                 max_rate_limit_retries=2, logger: logging.Logger = None):
        CrmClient.__init__(self, token=token, rate_limit=rate_limit,
                           max_rate_limit_retries=max_rate_limit_retries)
        self.list_id = list_id
        self.segment_id = segment_id
        # If logger argument is None, use default logger
        self._logger = logger or logging.getLogger(__name__)

    @property
    def klaviyo_identify_url(self):
        return self._KLAVIYO_IDENTIFY_URL

    @property
    def klaviyo_unsubscribe_url(self):
        return self._KLAVIYO_UNSUBSCRIBE_URL

    @property
    def klaviyo_track_url(self):
        return self._KLAVIYO_TRACK_URL

    @property
    def logger(self) -> logging.Logger:
        """ Returns the logger object to be used by the instance. """
        return self._logger

    def connect(self):
        """ Performs the necessary actions required to be able to make requests to Klaviyo.

        This method is automatically called when this class is used in a context manager i.e. when
        __enter__ is called.
        """
        self.session.mount('https://', self._retry_adapter(retries=3, backoff_factor=4))
        self.session.headers = self._build_base_header()

    def close(self):
        """  Performs necessary actions to terminate the connection with Klaviyo. """
        self.session.close()

    def _build_base_header(self) -> CaseInsensitiveDict:
        return CaseInsensitiveDict({
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'Authorization': f'Klaviyo-API-Key {self.get_private_api_key()}',
            'revision': '2024-07-15'
        })

    def get_public_api_key(self):
        return self.token['PUBLIC_API_KEY']

    def get_private_api_key(self):
        return self.token['PRIVATE_API_KEY']

    def get_public_private_api_key(self):
        return self.get_public_api_key(), self.get_private_api_key()

    def get_all_metrics(self) -> List[Dict]:
        """ Returns a list of all Klaviyo metrics as dictionaries.

            Returns:
                A list of dictionaries, where each dictionary represents a metric.
        """
        data = []
        page_cursor = None
        while not data or page_cursor:
            next_page_arg = get_next_page_cursor_arg(next_page=page_cursor)
            url = f'{KlaviyoMetric.metrics_info_url}?{next_page_arg}'
            res = self._request(method='GET', url=url).json()
            page_cursor = res['links']['next']
            data.extend(res['data'])
        return data

    def get_events(self, since_ts: str,
                   end_ts: str,
                   metric_name: str,
                   include: str = 'profile',
                   obj_to_get_from_inc: List = None,
                   metric_id: str = None):
        """ Gets all Klaviyo events for <metric_name>, during the period (<since_ts>, <end_ts>).

            Args:
                since_ts: A unix timestamp with the seconds since epoch in UTC. Marks the beginning
                    of the window for which we will extract event data.
                end_ts: A unix timestamp with the seconds since epoch in UTC. Marks the end of the
                    window for which we will extract event data. If set to None, then we extract
                    all data available since <since_ts>.
                metric_name: Name of the Klaviyo metric.
                include: if any additional fields are needed (e.g profile)
                obj_to_get_from_inc: A list of objects to get from the included field

            Returns:
                A list of event dictionaries.

            Raises:
                KlaviyoError if the metric with the specified name is not found.
        """
        # Get id of metric given the name
        if metric_id is None:
            metric_id = self.get_metric_id(metric_name=metric_name)

        # Configure URL and URL arguments to get events for <metric_id> since <since_ts>
        url_base = KlaviyoMetric.get_metric_events_url(metric_id)
        url_args = ''
        if since_ts:
            url_args += f"%2C{get_url_since_timestamp_filter_args(since_ts)}"
        if end_ts:
            url_args += f"%2C{get_url_until_timestamp_filter_args(end_ts)}"

        url = url_base + url_args
        url += f'&{KlaviyoMetric.include_template.substitute(value=include)}'
        # Get all events in batches
        event_list = []
        next_page = None
        while not event_list or next_page:
            # Get data with Klaviyo client
            res = self._request(method='GET', url=url).json()
            # Add data to list
            if obj_to_get_from_inc:
                for ob in obj_to_get_from_inc:
                    event_list.extend(get_field_from_included(res['data'],
                                                              res['included'],
                                                              f'attributes.properties.{ob}'))
            else:
                event_list.extend(res['data'])

            # If there are no more pages then break the loop
            if res['links']['next'] is None:
                break
            next_page = res['links']['next']
            url = next_page
            # Sleep for a bit - Klaviyo allows 350 calls per second before a rate limited error
            time.sleep(0.01)

        return event_list

    def get_metric_id(self, metric_name: str) -> str:
        """ Calls the Klaviyo API to get the metric id given a metric name.

        k_client: KlaviyoClient object for making the call.

        Returns:
            The metric id character string.

        Raises:
            KlaviyoError if the metric with the specified name is not found.
        """
        # Iterate over data and return correct metric_id
        metric_list = self.get_all_metrics()
        for metric in metric_list:
            if metric['attributes']['name'] == metric_name:
                return metric['id']
        raise KlaviyoMetricError(f'Metric with name {metric_name} not found.')

    def get_flow_id(self, flow_name: str) -> str:
        """ Calls the Klaviyo API to get the flow id given a flow name.

        k_client: KlaviyoClient object for making the call.

        Returns:
            The flow id character string.

        Raises:
            KlaviyoError if the flow with the specified name is not found.
        """
        encoded_flow_name = urllib.parse.quote(flow_name)
        flow_filter = f"&filter=equals(name,'{encoded_flow_name}')"
        url = f'{self._KLAVIYO_FLOWS_URL}{flow_filter}'
        res = self._request(method='GET', url=url).json()
        data = res.get('data', [])
        if data:
            # Extract the 'id' from 'data'
            flow_id = data[0].get('id')
            return flow_id
        else:
            raise KlaviyoMetricError(f'Flow with name {flow_name} not found.')

    def get_global_exclusions(self, count: int = 5000, max_pages: int = 50,
                              reason: str = '') -> List[Dict]:
        """ Returns global exclusions/unsubscribes.

         Global exclusions are distinct from list exclusions in that these email addresses will not
         receive any emails from any list.

         https://developers.klaviyo.com/en/reference/get-global-exclusions

        Args:
            count: The number of results to return.
            max_pages: The maximum amount of pages that is expected to contain all the unsubscribes,
                with <count> unsubscribes in each page.
            reason: The exclusion reason based on which we can filter which types of exclusions we
                want to retrieve by calling get_global_exclusions. The value of this should be
                a member of the EXCLUSION_REASONS list attribute of the KlaviyoClient class.

        Returns:
            A list of dictionaries where each dictionary represents a global unsubscribe.

        Raises:
            KlaviyoClientError if the exclusion reason is a non empty string that is not in the
                EXCLUSION_REASONS list attribute.
        """
        if reason and reason not in self.EXCLUSION_REASONS:
            raise KlaviyoClientError('The value provided to the get_global_exclusions call for'
                                     'the argument <reason> is not a member of the '
                                     'EXCLUSION_REASONS list attribute in KlaviyoClient.')
        unsubscribes_list = []
        for page_i in range(max_pages):
            url_args = (f'reason={reason}&count={count}&page={page_i}'
                        f'&api_key={self.get_private_api_key()}')
            url = f'{self.klaviyo_unsubscribe_url}?{url_args}'
            response = self._request(method="GET", url=url)
            unsubscribes_list.extend(response.json()['data'])
        return unsubscribes_list

    def update_profiles(self, update_data: List[Dict], company_id: str, store: str = 'N/A'):
        """ Updates the profile attributes specified in <update_data>

        Args:
            update_data: A list of dictionaries where each dictionary represents a profile and
                includes the attributes that are going to be updated and their corresponding values.
                In the dictionary we additionally expect an extra field called 'email' we use that
                for logging purposes in case the update fails. We then delete that from the dictio
                nary
            company_id: The public API key/ site ID to be used.
            store: Store name for which we run the update. This is used for logging failed updates.
        """

        def format_payload_json(record, **kwargs):
            email = record.pop('$email')
            record['email'] = email
            f = {
                'data':
                    {
                        'type': 'profile',
                        'attributes': {
                            "email": email,
                            'properties': record}
                    }
            }

            data = json.dumps(f, indent=4)
            return email, data

        self._klaviyo_request(update_data, store, url=f'{self._KLAVIYO_IDENTIFY_URL}{company_id}',
                              method=format_payload_json)

    def update_location(self, update_data: List[Dict], store: str = 'N/A'):
        """ Updates location information for a given user

        Args:
            update_data: A list of dictionaries where each dictionary contains information regarding
            the customer location (zip code, city e.t.c).

            store: Store name for which we run the update. This is used for logging failed updates.
        """

        def format_payload_json(record, **kwargs):
            email = record.pop('$email')
            f = {
                "type": "profile",
                "attributes": {
                    "email": email,
                    "location": {
                        k: v for k, v in record.items()
                    }
                }
            }
            return f

        successful = self._start_bulk_import_profile_job(
            format_method=format_payload_json,
            profiles=update_data
        )

        return successful

    def create_event_in_metric(self, update_data: List[Dict], store: str = 'N/A'):
        """ Updates a Klaviyo metric with event attributes specified in <update_data>

        Args:
            update_data: A list of dictionaries where each dictionary represents a customer's email,
            event name, metric name, token and also includes the attributes that are going to be
            updated and their corresponding values.
            store: Store name for which we run the update. This is used for logging failed updates.
        """

        def format_payload_json(record, **kwargs):
            email = record.pop('email')
            event_name = record.pop('event_name')
            f = {
                'data': {
                    'type': 'event',
                    'attributes': {
                        'properties': record,
                        'metric': {
                            'data': {
                                "type": "metric",
                                'attributes':
                                    {'name': event_name,
                                     }
                            }
                        },
                        'profile': {'data':
                                        {'type': 'profile',
                                         'attributes': {
                                             'email': email,
                                         }
                                         }
                                    }
                    }
                }
            }

            data = json.dumps(f, indent=4)
            return email, data

        self._klaviyo_request(update_data, store,
                              url=self._KLAVIYO_TRACK_URL + self.token['PUBLIC_API_KEY'],
                              method=format_payload_json)

    def _klaviyo_request(self, update_data: List[Dict], store: str,
                         url: str, method: Callable, **kwargs):
        """ Calls a request post method

               Args:
                   update_data: A list of dictionaries where each dictionary represents a
                       customer's profile and includes the attributes that are going to
                       be updated and their corresponding values.
                   store: Store name for which we run the update. This is used for logging
                       failed updates.
                   url: endpoint /api url
                   method: a callable function that returns a json formatted str.
               """
        for record in update_data:
            email, data = method(record, **kwargs)
            try:
                self._request(method='POST', url=url, data=data)
            except Exception as e:
                self.logger.exception(f"Failed to update {email} for {store} got exception {e}")

    def get_segment_members(self, extra_fields: List[tuple] = None) -> List[Dict]:
        """Get all members from the segment
        Args:
            'extra_fields': A list of the extra fields to return if any. The list should consist of
            tuples where each tuple is (field_name, field_path). The field name is the name which
            will be returned by the function and the field path should be the path that needs to be
            followed in order to fetch the value in the JSON seperated by '.'. So if for example we
            want to fetch a field named 'user_id' which lies under attributes.properties.user id
            then extra_fields = ('user_id','attributes.properties.user_id').
        Returns:
            A list of dictionaries where each dictionary corresponds to a member of the segment. E.g.
            [{'id': '01GCY4YJKP67R3ZEHAVEYC1KXK', 'email': 'test1@hayppgroup.com'},
             {'id': '01GD38S642GQW6TR46S30KBYNQ', 'email': 'test2@hayppgroup.com'}]
        """
        get_members_url = self._KLAVIYO_GET_SEGMENT_MEMBERS_URL_TEMPLATE.format(
            segment_id=self.segment_id
        )
        url = get_members_url
        # Use pagination to iterate over all members
        segment_members = []

        next_page = None
        while not segment_members or next_page:
            json_response = self._request(method='GET', url=url).json()
            if len(json_response['data']) == 0:
                break
            for data in json_response['data']:
                if not extra_fields:
                    segment_members.append({'id': data['id'],
                                            'email': data['attributes']['email']})
                else:
                    extra_fields_dict = {field[0]: get_value_from_path(data, field[1])
                                         for field in extra_fields}

                    segment_members.append({'id': data['id'],
                                            'email': data['attributes']['email'],
                                            **extra_fields_dict})
            next_page = json_response['links']['next']
            url = next_page

        return segment_members

    def get_list_members(self) -> List[Dict]:
        """ Gets all members from the list.

        Returns:
            A list of dictionaries where each dictionary corresponds to a member of the list. E.g.
            [{'id': '01GCY4YJKP67R3ZEHAVEYC1KXK', 'email': 'test1@hayppgroup.com'},
             {'id': '01GD38S642GQW6TR46S30KBYNQ', 'email': 'test2@hayppgroup.com'}]
        """
        get_members_url = self._KLAVIYO_GET_GROUP_MEMBERS_URL_TEMPLATE.format(
            list_id=self.list_id
        )
        url = get_members_url
        # Use pagination to iterate over all members
        list_members = []

        next_page = None
        while not list_members or next_page:
            json_response = self._request(method='GET', url=url).json()
            if len(json_response['data']) == 0:
                break
            list_members.extend([{'id': data['id'], 'email': data['attributes']['email']}
                                 for data in json_response['data']])
            next_page = json_response['links']['next']
            url = next_page
        return list_members

    def remove_list_members(self, list_id, members_payload):
        """ Removes specified members from a list.

        Args:
             list_id: the id of the list from which to remove members.
             members_payload: A dictionary where the key is a type of customer identifier (e.g.
             "emails"), and the value is a list with the identifier values (e.g. e-mail addresses)
             of the customers we want to delete. E.g.

             {"emails": ['test@hayppgroup.com', 'test2@hayppgroup.com']}
        """

        def _preprocess_payload(payload):
            return {'data': [{'type': 'profile',
                              **member} for member in payload]}

        url = self._KLAVIYO_LIST_MEMBERS_URL.substitute(id=list_id)
        return self._request(method='DELETE', url=url, json=_preprocess_payload(members_payload))

    def clean_list(self, list_id) -> bool:
        """ Clears the list.

            Returns:
                True if no exception is raised while clearing the list.
        """
        records = self.get_list_members()
        if not records:
            # Return because if we make a request with no records it will cause a 400 Bad Request
            return True
        self.remove_list_members(list_id=list_id,
                                 members_payload=records)
        return True

    def post_list_sync(self, list_data: List, import_type: str = 'ADD'):
        """ Posts a list of customers to the Klaviyo list.

        Args:
            import_type: This can be either 'ADD' or 'REPLACE'. Using 'ADD' will add new customers
                to the list, while 'REPLACE' will first clear the list and then add those new
                customers.
            list_data: A dictionary with two keys list_id and a  key ("profiles") which is
            mapped to a list of dictionaries where each dictionary corresponds to the customer
            profile we want to add to the list. The profile must have an identifier such as a mobile
             phone number or e-mail address to be added to the list. Uses the Klaviyo API function
             described in https://developers.klaviyo.com/en/reference/add-members.

        Returns:
            We return True if the call is successful. False, otherwise.

        Raises:
            AssertionError if import_type is not 'REPLACE' or 'ADD'.
        """

        def format_payload_json(records, **kwargs):
            f = {
                "data": {
                    "type": "profile-subscription-bulk-create-job",
                    "attributes": {
                        "profiles": {
                            "data": [
                                {
                                    "attributes": {
                                        **record
                                    }
                                }
                            ] for record in records
                        }
                    },
                    "relationships": {
                        "list": {
                            "data": {
                                "type": "list",
                                "id": list_id
                            }
                        }
                    }
                }
            }

            data = json.dumps(f, indent=4)
            return data

        list_id = self.list_id
        assert import_type in ('REPLACE', 'ADD')
        if import_type == 'REPLACE':
            self.clean_list(list_id=list_id)
        if not len(list_data):
            return True
        url = self._KLAVIYO_SUBSCRIBE_PROFILES
        self._request(method='POST', url=url, json=format_payload_json(list_data))
        return True

    def post_survey_candidates(self, **kwargs):
        """ Wrapper around create_event_in_metric. Used to achieve polymorphism with other CrmClient
        subclasses such as SymplifyClient. We do this because we might use different methods to post
        survey candidates in different CRM systems. """
        self.create_event_in_metric(**kwargs)
        return True

    def request_customer_deletion(self, email):
        """ Requests Klaviyo to delete  customers given their e-mails.
        Args:
            email: The email of the customer we want to delete from Klaviyo."""

        payload = {
            "data": {
                "type": "data-privacy-deletion-job",
                "attributes":
                    {"profile":
                        {"data": {
                            "type": "profile",
                            "attributes": {"email": email}
                        }}}
            }}

        url = self._KLAVIYO_REQUEST_PROFILE_DELETION_URL
        self._request(method='POST', url=url, json=payload)
        return True

    def bulk_subscribe_profiles(self, profiles: List[Any], list_id: str = None) -> bool:
        """
        Subscribe profiles to email communication from klaviyo in bulk.

        Rate limits:
            Burst: 75/s
            Steady: 700/m

        See klaviyo api docs:
            https://developers.klaviyo.com/en/reference/bulk_subscribe_profiles
        Args:
            profiles: A list of dictionary entries with user profile information from klaviyo.
                        Each entry must contain 'id' and 'email' as keys.
            list_id: The id of a list in klaviyo which all profiles will be added to.
                        This list_id is optional.

        Returns:
            True if method executes without failure
        """
        job_type = 'profile-subscription-bulk-create-job'
        url = self._KLAVIYO_SUBSCRIBE_PROFILES

        def format_profile(profile):
            email = profile['email']
            profile_id = profile['id']
            data = {
                "type": "profile",
                "id": profile_id,
                "attributes": {
                    "email": email,
                    "subscriptions": {
                        "email": {
                            "marketing": {
                                "consent": "SUBSCRIBED"
                            }
                        }
                    }
                }
            }
            return data

        chunks = chunk_list(profiles, 1000)

        for chunk in chunks:
            payload = self._get_payload_for_bulk_job(
                job_type=job_type,
                format_method=format_profile,
                profiles=chunk,
                list_id=list_id
            )

            response = self._request(method='POST', url=url, json=payload)
            response.raise_for_status()

        return True

    def bulk_create_events(self, data) -> bool:
        """
        Bulk create events to Klaviyo. Allowed payload size is 5MB

        Rate limits
            Burst: 10/s
            Steady: 150/m

        See klaviyo api docs:
            https://developers.klaviyo.com/en/reference/bulk_create_events

        Args:
            A list of dictionaries where each dictionary has the email or the klaviyo profile id
            along with the events data for a user.

        Returns:
            True if all jobs have completed successfully.
        """
        job_type = 'event-bulk-create-job'
        url = self._KLAVIYO_BULK_CREATE_EVENTS

        def format_events(event_properties):
            email = event_properties.pop('$email', '')
            # we can use either the kavliyo profile id or the email to identify the user
            klaviyo_profile_id = event_properties.pop('$id', '')
            event_name = event_properties.pop('event_name')
            time_of_event = str(event_properties.pop('$time', ''))
            events = {
                "type": "event-bulk-create",
                "attributes": {
                    "profile": {
                        "data": {
                            "type": "profile",
                            "attributes": {
                                "email": email,
                                "id": klaviyo_profile_id
                            }
                        }
                    },
                    "events": {
                        "data": [
                            {
                                "type": "event",
                                "attributes": {
                                    "properties": {
                                       **event_properties
                                    },
                                    "time": time_of_event,
                                    "metric": {
                                        "data": {
                                            "type": "metric",
                                            "attributes": {
                                                "name": event_name
                                            }
                                        }
                                    }
                                }
                            }
                        ]
                    }
                }
            }
            return events

        chunks = chunk_list(data, 1000)
        event_count = 0
        for chunk in chunks:
            payload = self._get_payload_for_bulk_event_job(
                job_type=job_type,
                format_method=format_events,
                events=chunk
            )
            try:
                event_count += 1
                response = self._request(method='POST', url=url, json=payload)
                response.raise_for_status()
            except Exception as e:
                self.logger.exception(f'Failed to create event chunk #{event_count} got exception {e}')

        self.logger.info(f'Created {event_count} chunks of events...')
        return True

    def bulk_import_profiles(self, profiles: List[Any], list_id: str = None) -> bool:
        """
        Bulk upsert profiles to klaviyo.

        Rate limits:
            Burst: 10/s
            Steady: 150/m

        See klaviyo api docs:
            https://developers.klaviyo.com/en/reference/spawn_bulk_profile_import_job

        Args:
            profiles: A list of dictionary entries with user profile information from klaviyo.
                        Each entry must contain 'id' and 'email' as keys.
            list_id: The id of a list in klaviyo which all profiles will be added to.
                        This list_id is optional.

        Returns:
            True if all import jobs complete successfully
        """

        def format_profile(attributes):
            email = attributes.pop('$email')
            # in case of missing keys, set them to None. Klaviyo will ignore None values
            # and therefore the profile will not be updated with these values.
            city = attributes.pop('city', None)
            country = attributes.pop('country', None)
            zipcode = attributes.pop('zip_code', None)
            region = attributes.pop('region', None)
            profile = {
                "type": "profile",
                "attributes": {
                    "email": email,
                    "properties": {
                        k: v for k, v in attributes.items()
                    },
                    "location": {
                        'city': city,
                        'country': country,
                        'zip': zipcode,
                        'region': region}
                }
            }
            return profile

        successful = self._start_bulk_import_profile_job(
            format_method=format_profile,
            profiles=profiles,
            list_id=list_id
        )

        return successful

    def _start_bulk_import_profile_job(self, format_method: Callable[[Any], dict],
                                       profiles: List[Any], list_id: str = None) -> bool:
        """
        Chunks bulk jobs and posts to klaviyo
        Args:
            format_method: method to format the payload correctly
            profiles: list of profiles to be sent to klaviyo
            list_id: id of list to insert profiles into (optional)

        Returns:
            True if all jobs complete successfully

        """
        job_type = 'profile-bulk-import-job'
        url = self._KLAVIYO_BULK_UPSERT_PROFILES_URL

        # chunk list
        chunks = chunk_list(profiles, 1000)

        jobs = []

        # process chunk in chunks
        for n, chunk in enumerate(chunks, 1):
            self.logger.info(f'Processing chunk {n}...')
            payload = self._get_payload_for_bulk_job(
                job_type=job_type,
                format_method=format_method,
                profiles=chunk,
                list_id=list_id
            )

            job_id = self._submit_bulk_import_profile_job(
                url=url,
                payload=payload
            )
            jobs.append(job_id)
            time.sleep(1)

        self.logger.info(f'Created {len(jobs)} jobs...')

        return True

    def _get_payload_for_bulk_event_job(self, job_type: str, format_method: Callable[[Any], dict],
                                        events: List[Any]) -> Dict:
        """
        Helper method to get the correctly formatted payload for a bulk event upload job.

        # Args:
            job_type: job type (see klaviyo api docs)
            format_method: method to format the event data correctly
            events: list of events to upload
        Returns
            Formatted payload to upload using bulk job.
        """
        payload = {
            "data": {
                "type": job_type,
                "attributes": {
                    "events-bulk-create": {
                        "data": [format_method(event) for event in events]
                    }
                }
            }
        }
        return payload

    def _get_payload_for_bulk_job(self, job_type: str, format_method: Callable[[Any], dict],
                                  profiles: List[Any], list_id: str = None):
        """
        Helper method to get the correctly formatted payload for a bulk upload job.
        Args:
            job_type: job type (see klaviyo api docs)
            format_method: method to format the profile data correctly
            profiles: list of profiles to upload
            list_id: id of list to insert profiles into (optional)

        Returns:
            Formatted payload to upload using bulk job.
        """
        payload = {
            "data": {
                "type": job_type,
                "attributes": {
                    "profiles": {
                        "data": [format_method(profile) for profile in profiles]
                    }
                }
            }
        }

        if list_id:
            payload['data']['relationships'] = {
                "lists": {
                    "data": [
                        {
                            "type": "list",
                            "id": list_id
                        }
                    ]
                }
            }

        return payload

    def _submit_bulk_import_profile_job(self, url: str, payload: Dict) -> str:
        """
        Submit bulk import profile job
        Args:
            url: endpoint to post to
            payload: payload

        Returns:
            The job_id of the bulk import job created
        """
        response = self._request(method='POST', url=url, json=payload)
        response.raise_for_status()

        job_id = response.json()['data']['id']

        return job_id

    def get_list_members_count(self) -> tuple:
        """ Returns the number of members in a Klaviyo list.

        Returns:
            The nname of the list along with it's member count
        """
        url = self._KLAVIYO_LIST_MEMBERS_COUNT.replace('id', self.list_id)
        response = self._request(method='GET', url=url)
        profile_count = response.json()['data']['attributes']['profile_count']
        list_name = response.json()['data']['attributes']['name']
        self.logger.info(f'Got list with name {list_name} has {profile_count} members.')
        return list_name, profile_count

    def get_segment_members_count(self) -> tuple:
        """ Returns the number of members in a Klaviyo segment.

        Returns:
            The name of the segment along with it's member count
        """
        url = self._KLAVIYO_SEGMENT_MEMBERS_COUNT.replace('id', self.segment_id)
        response = self._request(method='GET', url=url)
        profile_count = response.json()['data']['attributes']['profile_count']
        segment_name = response.json()['data']['attributes']['name']
        self.logger.info(f'Got segment with name {segment_name} has {profile_count} members.')
        return segment_name, profile_count

    def get_email_campaigns(self,
                            include_messages=True) -> Tuple[List[Dict], List[Dict]]:
        """
        Returns a tuple of all campaigns and campaign messages from a Klaviyo site. If
        include_messages = False then only the campaigns are returned.

        Rate Limits:
            Burst: 10/s
            Steady: 150/m
        """
        base_url = self._KLAVIYO_CAMPAIGNS_URL
        filter_url = get_filter_url('equals',
                                    'messages.channel',
                                    "'email'")
        # we need to include campaign messages to get the message id of the variation if there
        # is one
        email_campaigns_url = f"{base_url}?filter={filter_url}"
        if include_messages:
            email_campaigns_url += "&include=campaign-messages"

        campaign_list = []
        campaign_messages_list = []
        next_page = None
        while not campaign_list or next_page:
            # Get data with Klaviyo client
            res = self._request(method='GET', url=email_campaigns_url).json()
            # Add data to list

            campaign_list.extend(res['data'])
            if include_messages:
                campaign_messages_list.extend(res['included'])
            # If there are no more pages then break the loop
            if res['links']['next'] is None:
                break
            next_page = res['links']['next']
            email_campaigns_url = next_page
            # Sleep for a bit - Klaviyo allows 350 calls per second before a rate limited error
            time.sleep(0.01)
        return campaign_list, campaign_messages_list
