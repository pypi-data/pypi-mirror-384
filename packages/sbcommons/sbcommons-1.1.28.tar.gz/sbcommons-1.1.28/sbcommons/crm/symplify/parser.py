from typing import Any
from typing import List
from typing import Iterable

from sbcommons.crm.parser import CrmParser
from sbcommons.crm.parser import TranslationEntry


class SymplifyParser(CrmParser):
    """ Class for parsing query results into a format compatible with the SymplifyClient.

    Attributes:
        translation_dict: A dictionary that maps a database column name to a TranslationEntry,
            which is used to rename the column to the right name for Symplify and cast its
            values to the right data type. Inherited from Parser.
        delimiter: What delimiter to use to separate fields when parsing the input.
    """
    def __init__(self, translation_entries: List[TranslationEntry], delimiter: str = '|'):
        CrmParser.__init__(self, translation_entries)
        self.delimiter = delimiter

    def source_headers(self) -> List[str]:
        """ Returns the column names as expected from the query results. """
        return [db_column_name for db_column_name in self.translation_dict]

    def parse(self, header: List[str], rows: List[Iterable[Any]]) -> bytes:
        """ Converts the <header> and <rows> to a format compatible with SymplifyClient.

        Args:
            header: The column names for each field in <rows>.
            rows: A list of iterables where each iterable has the values specified by the <header>.

        Returns:
            A byte sequence that can be used in SymplifyClient calls such as a post_list_sync call.
        """
        parsed_header = self.parse_header(header)
        header_str = self.delimiter.join(parsed_header)
        plain_text_data = '\n'.join([header_str] + [self._parse_row(header, row) for row in rows])
        return plain_text_data.encode('utf-8')

    def _parse_row(self, header: List[str], row: Iterable[Any]):
        return f'{self.delimiter}'.join([self._sanitize(db_column_name, val, self.delimiter)
                                         for db_column_name, val in zip(header, row)])
