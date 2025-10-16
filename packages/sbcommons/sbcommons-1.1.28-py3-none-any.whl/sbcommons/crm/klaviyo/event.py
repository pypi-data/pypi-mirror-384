""" Class representing an event on Klaviyo """
from abc import ABC, abstractmethod
from functools import reduce
from typing import Dict
from typing import List

import pandas as pd


class KlaviyoEvent(ABC):
    """ Base Klaviyo event class"""

    @classmethod
    @property
    @abstractmethod
    def metric_name(cls) -> str:
        """ The name of the metric the event corresponds to. """
        raise NotImplementedError

    @classmethod
    @property
    @abstractmethod
    def column_paths(cls):
        """ A dict that maps the path of each event json column to the name of that column. """
        raise NotImplementedError

    @staticmethod
    def get_json_col(json_dict: dict, column_path: str) -> str:
        """ Extracts the element in the json string specified by <column_path>

        Args:
            json_dict: A dict corresponding to the json file.
            column_path: The path to the element we want to extract. E.g. column_path = x.y.z if we
                want to extract value from {x: {y: {z: value}}}.

        """
        return reduce(lambda d, key: d.get(key) if d else None, column_path.split('.'), json_dict)

    @classmethod
    def events_to_df(cls, events_list: List[dict]):
        """ Converts the metric events in events_list to a pandas DataFrame.

        events_list: A list of json files where each json file represents an event.

        Returns:
            A pandas DataFrame with a number of columns extracted from each event specified by
                <column_paths>. For example, for ReceivedKlaviyoEvent we extract the following
                columns: i) campaign_name, customer_id_hash, message_sendtime.
        """
        parsed_events = []
        for event in events_list:
            parsed_event = {}
            for column_path, column_name in cls.column_paths.items():
                column_value = cls.get_json_col(event, column_path)
                parsed_event[column_name] = column_value if column_value else ''
            parsed_events.append(parsed_event)
        df_columns = list(parsed_event.keys()) if events_list else []
        df = pd.DataFrame(parsed_events, columns=df_columns)
        return df

    @classmethod
    def get_event_class_by_metric_name(cls, metric_name: str):
        """ Gets a KlaviyoEvent object (subclass) given the metric name.

        Args:
            metric_name: The name of the metric.

        Returns:
            A KlaviyoEvent subclass where the metric_name property is equal to the metric_name
            argument passed into this function. E.g. if <metric_name> == 'Received Email',
            the function returns ReceivedKlaviyoEvent.
        """
        for klaviyo_event in KlaviyoEvent.__subclasses__():
            if klaviyo_event.metric_name == metric_name:
                return klaviyo_event


class ProductTracker(KlaviyoEvent):
    """ A product tracker trigger event that sends out survey invitation.

    Attributes:
        column_paths (Dict[str, str]): A dictionary that maps different paths of the event json
            (e.g. event_properties.Campaign_Name) to the variable names in snake case
            (e.g. campaign_name).
        original_id (str): Survey customer id hash passed from survey tracker handler run.
        datetime (str): datetime of the trigger in Klaviyo.
        profile_id (str): native customer id in Klaviyo.
    """

    column_paths = {
        'attributes.event_properties.originalId': 'original_id',
        'attributes.datetime': 'datetime',
        'relationships.profile.data.id': 'profile_id',
        'flow_id': 'flow_id'
    }

    def __init__(self, original_id: str, datetime: str, profile_id: str, flow_id: str):
        KlaviyoEvent.__init__(self)
        self.original_id = original_id
        self.datetime = datetime
        self.profile_id = profile_id
        self.flow_id = flow_id

    @classmethod
    @property
    def metric_name(cls) -> str:
        """ The name of the metric the event corresponds to. """
        return 'Product Tracker Flow'


class BrandTracker(KlaviyoEvent):
    """ A brand tracker trigger event that sends out survey invitation.

    Attributes:
        column_paths (Dict[str, str]): A dictionary that maps different paths of the event json
            (e.g. event_properties.Campaign_Name) to the variable names in snake case
            (e.g. campaign_name).
        original_id (str): Survey customer id hash passed from survey tracker handler run.
        datetime (str): datetime of the trigger in Klaviyo.
        profile_id (str): native customer id in Klaviyo.
    """

    column_paths = {
        'attributes.event_properties.originalId': 'original_id',
        'attributes.datetime': 'datetime',
        'relationships.profile.data.id': 'profile_id',
        'flow_id': 'flow_id'
    }

    def __init__(self, original_id: str, datetime: str, profile_id: str, flow_id: str):
        KlaviyoEvent.__init__(self)
        self.original_id = original_id
        self.datetime = datetime
        self.profile_id = profile_id
        self.flow_id = flow_id


    @classmethod
    @property
    def metric_name(cls) -> str:
        """ The name of the metric the event corresponds to. """
        return 'Brand Tracker Flow'


class ChurnTracker(KlaviyoEvent):
    """ A churn tracker trigger event that sends out survey invitation.

    Attributes:
        column_paths (Dict[str, str]): A dictionary that maps different paths of the event json
            (e.g. event_properties.Campaign_Name) to the variable names in snake case
            (e.g. campaign_name).
        original_id (str): Survey customer id hash passed from survey tracker handler run.
        datetime (str): datetime of the trigger in Klaviyo.
        profile_id (str): native customer id in Klaviyo.
    """

    column_paths = {
        'attributes.event_properties.originalId': 'original_id',
        'attributes.datetime': 'datetime',
        'relationships.profile.data.id': 'profile_id',
        'flow_id': 'flow_id'
    }

    def __init__(self, original_id: str, datetime: str, profile_id: str, flow_id: str):
        KlaviyoEvent.__init__(self)
        self.original_id = original_id
        self.datetime = datetime
        self.profile_id = profile_id
        self.flow_id = flow_id

    @classmethod
    @property
    def metric_name(cls) -> str:
        """ The name of the metric the event corresponds to. """
        return 'Churn Tracker'


class ReceivedEmail(KlaviyoEvent):
    """ An event corresponding to the received e-mail metric

    Attributes:
        column_paths (Dict[str, str]): A dictionary that maps different paths of the event json
            (e.g. event_properties.Campaign_Name) to the variable names in snake case
            (e.g. campaign_name).
        customer_id_hash (str): Customer id hash of the customer who got received the e-mail.
        campaign_name (str): Campaign name of the campaign the customer received by e-mail.
        message_sendtime (str): The time and date when the e-mail was received.
        profile_id (str): Klaviyo's local customer id.
        flow_id (str): The flow id of the relevant trigger flow if applicable.
        message_id (str): The message id of the e-mail.
    """

    column_paths = {
        'attributes.event_properties.Campaign Name': 'campaign_name',
        'customerhashID': 'customer_id_hash',
        'attributes.datetime': 'message_sendtime',
        'relationships.profile.data.id': 'profile_id',
        'attributes.event_properties.$flow': 'flow_id',
        'attributes.event_properties.$message': 'message_id',
        'attributes.event_properties.$variation': 'campaign_variation_message_id'
    }

    def __init__(self, customer_id_hash: str, campaign_name: str, message_sendtime: str,
                 profile_id: str, flow_id: str, message_id: str):
        KlaviyoEvent.__init__(self)
        self.customer_id_hash = customer_id_hash
        self.campaign_name = campaign_name
        self.message_sendtime = message_sendtime
        self.profile_id = profile_id
        self.flow_id = flow_id
        self.message_id = message_id

    @classmethod
    @property
    def metric_name(cls) -> str:
        """ The name of the metric the event corresponds to. """
        return 'Received Email'


class OpenedEmail(KlaviyoEvent):
    """ An event corresponding to the opened e-mail metric

     Attributes:
        column_paths (Dict[str, str]): A dictionary that maps different paths of the event json
            (e.g. event_properties.Campaign_Name) to the variable names in snake case
            (e.g. campaign_name).
        customer_id_hash (str): Customer id hash of the customer who got received the e-mail.
        campaign_name (str): Campaign name of the campaign the customer received by e-mail.
        message_sendtime (str): The time and date when the e-mail was received.
        profile_id (str): Klaviyo's local customer id.
        flow_id (str): The flow id of the relevant trigger flow if applicable.
        message_id (str): The message id of the e-mail.
    """

    column_paths = {
        'attributes.event_properties.Campaign Name': 'campaign_name',
        'customerhashID': 'customer_id_hash',
        'attributes.datetime': 'message_openedtime',
        'relationships.profile.data.id': 'profile_id',
        'attributes.event_properties.$flow': 'flow_id',
        'attributes.event_properties.$message': 'message_id',
        'attributes.event_properties.$variation': 'campaign_variation_message_id'
    }

    def __init__(self, customer_id_hash: str, campaign_name: str, message_openedtime: str,
                 profile_id: str, flow_id: str, message_id: str):
        KlaviyoEvent.__init__(self)
        self.customer_id_hash = customer_id_hash
        self.campaign_name = campaign_name
        self.message_openedtime = message_openedtime
        self.profile_id = profile_id
        self.flow_id = flow_id
        self.message_id = message_id

    @classmethod
    @property
    def metric_name(cls) -> str:
        """ The name of the metric the event corresponds to. """
        return 'Opened Email'


class ClickedEmail(KlaviyoEvent):
    """ An event corresponding to the clicked e-mail metric.

    Attributes:
        column_paths (Dict[str, str]): A dictionary that maps different paths of the event json
            (e.g. event_properties.Campaign_Name) to the variable names in snake case
            (e.g. campaign_name).
        customer_id_hash (str): Customer id hash of the customer who got received the e-mail.
        campaign_name (str): Campaign name of the campaign the customer received by e-mail.
    """

    column_paths = {
        'attributes.event_properties.Campaign Name': 'campaign_name',
        'customerhashID': 'customer_id_hash',
        'attributes.event_properties.$variation': 'campaign_variation_message_id'
    }

    def __init__(self, customer_id_hash: str, campaign_name: str):
        KlaviyoEvent.__init__(self)
        self.customer_id_hash = customer_id_hash
        self.campaign_name = campaign_name

    @classmethod
    @property
    def metric_name(cls) -> str:
        """ The name of the metric the event corresponds to. """
        return 'Clicked Email'


class Unsubscribed(KlaviyoEvent):
    """ An event corresponding to the 'Unsubscribed' metric.

    Attributes:
        column_paths (Dict[str, str]): A dictionary that maps different paths of the event json
            (e.g. event_properties.Campaign_Name) to the variable names in snake case
            (e.g. campaign_name).
        metric_name (str): The name of the metric the event corresponds to.
    """

    column_paths = {
        'customerhashID': 'customer_id_hash',
        'attributes.datetime': 'datetime'
    }

    def __init__(self, customer_id_hash: str, event_time: str):
        KlaviyoEvent.__init__(self)
        self.customer_id_hash = customer_id_hash
        self.event_time = event_time

    @classmethod
    @property
    def metric_name(cls) -> str:
        """ The name of the metric the event corresponds to. """
        return 'Unsubscribed'


class UnsubscribedFromSMS(KlaviyoEvent):
    """ An event corresponding to the 'Unsubscribed from SMS' metric.

    Attributes:
        column_paths (Dict[str, str]): A dictionary that maps different paths of the event json
            (e.g. event_properties.Campaign_Name) to the variable names in snake case
            (e.g. campaign_name).
        metric_name (str): The name of the metric the event corresponds to.
    """

    column_paths = {
        'customerhashID': 'customer_id_hash',
        'attributes.datetime': 'datetime'
    }

    def __init__(self, customer_id_hash: str, event_time: str):
        KlaviyoEvent.__init__(self)
        self.customer_id_hash = customer_id_hash
        self.event_time = event_time

    @classmethod
    @property
    def metric_name(cls) -> str:
        """ The name of the metric the event corresponds to. """
        return 'Unsubscribed from SMS'


class UnsubscribedFromList(KlaviyoEvent):
    """ An event corresponding to the 'Unsubscribed from List' metric.

    Attributes:
        column_paths (Dict[str, str]): A dictionary that maps different paths of the event json
            (e.g. event_properties.Campaign_Name) to the variable names in snake case
            (e.g. campaign_name).
        metric_name (str): The name of the metric the event corresponds to.
    """

    column_paths = {
        'attributes.event_properties.List': 'list_name',
        'customerhashID': 'customer_id_hash',
        'attributes.datetime': 'datetime'
    }

    def __init__(self, customer_id_hash: str, list_name: str, datetime: str):
        KlaviyoEvent.__init__(self)
        self.customer_id_hash = customer_id_hash
        self.list_name = list_name
        self.datetime = datetime

    @classmethod
    @property
    def metric_name(cls) -> str:
        """ The name of the metric the event corresponds to. """
        return 'Unsubscribed from List'


class SubscribedToList(KlaviyoEvent):
    """ An event corresponding to the 'subscribed to list' metric.

    Attributes:
        column_paths (Dict[str, str]): A dictionary that maps different paths of the event json
            (e.g. event_properties.Campaign_Name) to the variable names in snake case
            (e.g. campaign_name).
        metric_name (str): The name of the metric the event corresponds to.
    """

    column_paths = {
        'attributes.event_properties.List': 'list_name',
        'customerhashID': 'customer_id_hash',
        'attributes.datetime': 'datetime'
    }

    def __init__(self, customer_id_hash: str, list_name: str, datetime: str):
        KlaviyoEvent.__init__(self)
        self.customer_id_hash = customer_id_hash
        self.list_name = list_name
        self.event_time = datetime

    @classmethod
    @property
    def metric_name(cls) -> str:
        """ The name of the metric the event corresponds to. """
        return 'Subscribed to List'
