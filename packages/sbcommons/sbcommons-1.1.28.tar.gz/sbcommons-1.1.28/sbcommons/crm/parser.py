from abc import ABC, abstractmethod
from datetime import datetime
import enum
from typing import Any
from typing import List
from typing import Iterable


class DataType(enum.Enum):
    STRING = str
    TIMESTAMP = datetime


class TranslationEntry:
    def __init__(self, db_column: str,
                 crm_attr_name: str,
                 data_type: DataType,
                 timestamp_format: str = None):
        self.db_column = db_column
        self.crm_attr_name = crm_attr_name
        self.data_type = data_type
        if data_type.value == datetime:
            assert timestamp_format is not None
            self.timestamp_format = timestamp_format


class CrmParser(ABC):
    """
    Attributes:
        translation_dict: A dictionary that maps a database column name to a TranslationEntry,
            which is used to rename the column to the right name for the CRM client and cast its
            values to the right data type.
    """
    def __init__(self, translation_entries: List[TranslationEntry]):
        self.translation_dict = {entry.db_column: entry for entry in translation_entries}

    def parse_header(self, header: List[str]) -> List[str]:
        """ Parses header, translating each column name to the right CRM attribute name """
        return [self.translation_dict[x].crm_attr_name for x in header]

    @abstractmethod
    def parse(self, header: List[str], rows: List[Iterable[Any]]):
        pass

    def _sanitize(self, db_column_name: str, row_val: Any, delimiter: str = '') -> str:
        data_type = self.translation_dict[db_column_name].data_type
        if row_val:
            if data_type.value == str:
                row_val = str(row_val).replace(delimiter, '')
            elif data_type.value == datetime:
                ts_format = self.translation_dict[db_column_name].timestamp_format
                row_val = row_val.strftime(ts_format)
        elif row_val is None:
            row_val = str(row_val).replace('None', '')

        return str(row_val)
