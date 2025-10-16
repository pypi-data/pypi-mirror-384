from string import Template
from  urllib.parse import quote

_FILTER_TEMPLATE = Template('$condition($metric_id,$metric_value)')
_PAGE_CURSOR_ARG_TEMPLATE = Template('?page[cursor]=$page_cursor')
_SORT_ARG_TEMPLATE = Template('sort=$sort_criterion')
_FIELD_ARG_TEMPLATE = Template('fields[$metric]=$value')


def get_field_arg(metric, value):
    return _FIELD_ARG_TEMPLATE.substitute(metric=metric,
                                          value=value)


def get_filter_url(condition, metric_id, metric_value):
    return _FILTER_TEMPLATE.substitute(condition=condition,
                                       metric_id=metric_id,
                                       metric_value=quote(metric_value))


def get_sort_arg(sort_criterion):
    """ Gets the argument string for the Klaviyo API call given the parameters

            Args:
                sort_criterion: Which field name to use for sorting. E.g datetime will sort by datetime ascending
                    while -datetime will sort based on datetime descending.

            Returns:
                The part of the Klaviyo API call URL corresponding to the call parameters. E.g.
                    sort=datetime
            """
    return _SORT_ARG_TEMPLATE.substitute(sort_criterion=sort_criterion)


def get_url_since_timestamp_filter_args(since: str):
    """ Gets the filters part of the URL given the parameters

    Args:
        since: It's a Unix timestamp (UTC) that corresponds to the timestamp filter along
            with the 'greater-or-equal' option.It filters the events that happened after that
            timestamp
    """
    return get_filter_url(condition='greater-or-equal',
                          metric_id='timestamp',
                          metric_value=since)


def get_url_until_timestamp_filter_args(until: str):
    """ Gets the filters part of the URL given the parameters

    Args:
        until: It's a Unix timestamp (UTC) that corresponds to the timestamp filter along
            with the 'less-or-equal' option.It filters the events that happened before that
            timestamp
    """
    return get_filter_url(condition='less-or-equal',
                          metric_id='timestamp',
                          metric_value=until)


def get_next_page_cursor_arg(next_page: str = None):
    if next_page:
        return _PAGE_CURSOR_ARG_TEMPLATE.substitute(page_cursor=next_page)
    return ''
