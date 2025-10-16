""" Class definition for a Klaviyo metric """
from abc import ABC
import logging
from string import Template
from sbcommons.crm.klaviyo.url import (get_filter_url,get_url_since_timestamp_filter_args,
                                       get_url_until_timestamp_filter_args,
                                       get_next_page_cursor_arg)
from urllib.parse import quote


class KlaviyoMetricError(Exception):
    """ Klaviyo metric exception class"""

    def __init__(self, msg):
        super(KlaviyoMetricError, self).__init__(msg)


class KlaviyoMetric(ABC):
    """ Base class for a Klaviyo metric

    Attributes:
        metric_name: Name of the Klaviyo metric.
    """
    # Metric related URLs and URL-templates used to make Klaviyo API calls
    _METRICS_INFO_URL = 'https://a.klaviyo.com/api/metrics/'
    _METRIC_EVENTS_BASE_URL = 'https://a.klaviyo.com/api/events/'
    _FILTER_TEMPLATE = Template('filter=$condition($metric_id,$metric_value)')
    _INCLUDE_TEMPLATE = Template('include=$value')

    def __init__(self, metric_name: str):
        self.metric_name = metric_name
        self._logger = logging.getLogger(__name__)

    @classmethod
    @property
    def include_template(cls):
        return cls._INCLUDE_TEMPLATE

    @classmethod
    @property
    def metrics_info_url(cls):
        return cls._METRICS_INFO_URL

    @classmethod
    @property
    def metric_events_url(cls):
        return cls._METRICS_INFO_URL

    @classmethod
    def get_metric_events_url(cls, metric_id: str):
        """ Constructs URL for getting metric events given a metric identifier. """
        return cls._METRIC_EVENTS_BASE_URL + f"?filter=" + get_filter_url(condition='equals',
                                                                          metric_id='metric_id',
                                                                          metric_value=
                                                                          f'"{metric_id}"')


    @classmethod
    def get_metrics_info_url_args(cls, page_cursor: str):
        return get_next_page_cursor_arg(page_cursor)

