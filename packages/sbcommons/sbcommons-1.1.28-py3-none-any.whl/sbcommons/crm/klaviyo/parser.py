from typing import Any
from typing import Dict
from typing import Iterable
from typing import List

from sbcommons.crm.parser import CrmParser
from sbcommons.crm.parser import TranslationEntry


class KlaviyoParser(CrmParser):
    def __init__(self, translation_entries: List[TranslationEntry]):
        CrmParser.__init__(self, translation_entries)

    def parse(self, header: List[str], rows: List[Iterable[Any]]) -> List[Dict]:
        """
        list_data: A list of dictionaries where each dictionary corresponds to the customer
                profile we want to add to the list. The profile must have an identifier such as
                a mobile phone number or e-mail address to be added to the list.
        """
        return [self._parse_row(header, row) for row in rows]

    def _parse_row(self, header: List[str], row: Iterable[Any]) -> Dict[str, str]:
        f = {
            self.translation_dict[db_column_name].crm_attr_name: self._sanitize(db_column_name, val)
            for db_column_name, val in zip(header, row)
        }
        return f
