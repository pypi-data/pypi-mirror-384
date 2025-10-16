from abc import ABC
from functools import reduce
from typing import Dict
from typing import List

import pandas as pd


class KlaviyoCampaignParser(ABC):
    """ Class representing a klaviyo campaign related object (e.g. campaign or campaign message)."""
    def __init__(self):
        self.column_paths: Dict[str, str] = {'': ''}

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
    def campaigns_to_df(cls, campaigns_list: List[dict]):
        """ Converts a list of dictionaries representing campaign related objects
         (e.g campaigns or campaign messages)to a pandas DataFrame.

        campaigns_list: A list of json files where each json file represents an event.

        Returns:
            A pandas DataFrame with a number of columns extracted from each event specified by
                <column_paths>. For example, for ReceivedKlaviyoEvent we extract the following
                columns: i) campaign_name, customer_id_hash, message_sendtime.
        """
        parsed_campaigns = []

        for campaign in campaigns_list:
            parsed_campaign = {}
            try:
                for column_path, column_name in cls.column_paths.items():
                    column_value = cls.get_json_col(campaign, column_path)
                    parsed_campaign[column_name] = column_value if column_value else ''
                parsed_campaigns.append(parsed_campaign)
            except AttributeError as e:
                raise Exception(f"Error for column_path {column_path}: {e}")
        df_columns = list(parsed_campaign.keys()) if campaigns_list else []
        df = pd.DataFrame(parsed_campaigns, columns=df_columns)
        return df


class KlaviyoCampaign(KlaviyoCampaignParser):
    column_paths = {
        'id': 'campaign_id',
        'attributes.name': 'campaign_name',
        'attributes.status': 'campaign_status',
        'attributes.archived': 'is_archived',
        'attributes.created_at': 'campaign_created_at',
        'attributes.updated_at': 'campaign_updated_at',
        'attributes.send_time': 'campaign_sent_at',
    }

    def __init__(self):
        KlaviyoCampaignParser.__init__(self)


class KlaviyoCampaignMessage(KlaviyoCampaignParser):
    column_paths = {
        'id': 'message_id',
        'attributes.label': 'message_label',
        'relationships.campaign.data.id': 'campaign_id',
        'attributes.created_at': 'message_create_time',
        'attributes.updated_at': 'message-updated_at',
    }

    def __init__(self):
        KlaviyoCampaignParser.__init__(self)
