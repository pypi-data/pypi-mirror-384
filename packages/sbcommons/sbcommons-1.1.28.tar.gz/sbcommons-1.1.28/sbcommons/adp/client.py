import csv
import gzip
import io
import os
from typing import Any
from typing import Iterable
from typing import List
from typing import NamedTuple
from typing import Tuple


import pyodbc
from dataclasses import dataclass
from sbcommons.aws.s3 import put_object, get_object
from sbcommons.parse_utils import get_text_from_file
from sbcommons.utils import get_date_string, clear_s3_path


@dataclass
class ResponseRecord(NamedTuple):
    """Class for keeping track of a survey response record."""
    response_id: str
    filled_in_time: str  # datetime
    survey_type: str
    subgroup: str
    customer_id: str
    project_id: str
    survey_customer_id_hash: str
    status: str

    @classmethod
    def transform(cls: 'ResponseRecord',
                  field_cols: Iterable,
                  field_vals: Iterable) -> tuple:
        """ Casts each value in <field_vals> to the correct type specified by
            the ResponseRecord class definition.

            Args:
                field_cols (list): List of column values corresponding to the attribute names of
                     the ResponseRecord class.
                field_vals (list): List of values for each one of the columns in <field_cols> that
                    are casted to their correct type specified by the ResponseRecord class.


            Returns:
                A tuple with the <field_vals> items casted to the correct data type.
        """
        return tuple(cls.__annotations__[field_cols[i]](field)
                     for i, field in enumerate(field_vals))


class AdpClient:
    """ Client class for connecting to the ADP survey database, making queries and uploading data
    to S3 in a csv.gz format

    Attributes:
        conn (pyodbc.Connection): Connection object.
    """

    def __init__(self,
                 odbc_driver: str,
                 sql_server_host: str,
                 sql_server_port: str,
                 sql_database_name: str,
                 sql_uid: str,
                 sql_pwd: str):
        """

            Args:
                odbc_driver (str): Path to the odbc driver to use for connecting to the database.
                sql_server_host (str): Host name of the SQL server.
                sql_server_port (str): Port number of the SQL server.
                sql_database_name (str): Name of database to connect to.
                sql_uid (str): Login username to use for connecting.
                sql_pwd (str): Login password to use for connecting.
                s3_bucket (str): Name of S3 bucket where query results are stored.
                s3_dir_key (str): S3 key of directory where query results are stored within
                    <s3_bucket>.
        """
        # Create connection to server
        connect_string = 'DRIVER=' + odbc_driver + \
                         ';SERVER=' + sql_server_host + \
                         ';DATABASE=' + sql_database_name + \
                         ';UID=' + sql_uid + \
                         ';PWD=' + sql_pwd + \
                         ';PORT=' + sql_server_port
        self.conn = pyodbc.connect(connect_string)

    def execute_select(self, query) -> Tuple[List[str], List[Tuple[Any]]]:
        """ Executes given select query and returns the columns and rows.

        Returns:
            A (list, list) tuple where the first list is the columns and the second list of tuples
                is the rows returned by the select query.
        """
        cursor = self.conn.cursor()
        cursor.execute(query)
        columns = [column[0] for column in cursor.description]
        rows = [tuple(row) for row in cursor.fetchall()]
        cursor.close()
        return columns, rows

    def execute_select_from_text(self, sql_path: str, format_params: dict = None) \
            -> Tuple[List[str], List[Any]]:
        """ Executes a select query that returns the survey response data.

        Args:
            sql_path: Path to the sql file with the query to execute.
            format_params: Dictionary of parameters for formatting the query in <sql_path>.

        Returns:
            A (list, list) tuple where the first element includes the columns and the second element
                includes the rows returned by the select query.
        """
        query = get_text_from_file(sql_path)
        query = query.format(**format_params) if format_params else query
        return self.execute_select(query)

    @classmethod
    def query_results_to_s3(cls,
                            columns: List[str],
                            rows: List[Any],
                            s3_bucket: str,
                            s3_dir_key: str,
                            delimiter: str = '|',
                            file_base_name: str = "adp_dump",
                            should_clear_s3_path: bool = True,
                            backup_bucket: str = None) -> str:
        """ Uploads query results to a csv file on S3 gzipped.

        Args:
            columns (list): List of strings with the column string names written on the top of the
                 csv file.
            rows (list): List of elements returned in each row of a select statement.
            s3_bucket (str): Name of S3 bucket where query results are stored.
            s3_dir_key (str): S3 key of directory where query results are stored within <s3_bucket>.
            delimiter (str): Delimiter to be used for csv output file.
            file_base_name (str): Base name of csv.gzip file to be uploaded on S3 with the query
                results. A date is also appended to the name so that the final uploaded file name
                has the format: <file_base_name>__<DD_MM_YYYY>.csv.gz.
            should_clear_s3_path (bool): Set to true if you want to clear the S3 path before
                before uploading the new file, backing up the old data under <backup_bucket>.
            backup_bucket (str): If <should_clear_s3_path> is set to True, we clear the S3
                directory where the new file is uploaded, and save all files previously stored
                there under <backup_bucket>.

        Returns:
            S3 URL of the uploaded file.
        """
        # Create byte string of the data in gzip compressed csv format
        results = [columns] + rows
        buffer = io.BytesIO()
        with gzip.GzipFile(fileobj=buffer, mode='wb') as gzip_buffer:
            with io.TextIOWrapper(gzip_buffer, encoding='utf-8') as wrapper:
                csv_writer = csv.writer(wrapper, delimiter=delimiter, lineterminator='\n',
                                        quoting=csv.QUOTE_NONNUMERIC)
                csv_writer.writerows(results)

        # Create full name of file to be uploaded including timestamp
        timestamp_str = get_date_string()
        file_name = f"{file_base_name}__{timestamp_str}.csv.gz"

        # Keep backup of previous dump and upload new results to S3
        if should_clear_s3_path:
            clear_s3_path(s3_bucket, s3_dir_key, backup_bucket)
        object_key = os.path.join(s3_dir_key, file_name)
        put_object(bucket_name=s3_bucket, key=object_key, content=buffer.getvalue())
        return f"s3://{s3_bucket}/{object_key}"

    @classmethod
    def s3_to_query_results(cls,
                            s3_bucket: str,
                            s3_dir_key: str,
                            s3_file_name: str,
                            delimiter: str = '|'
                            ) -> Tuple[List[str], List[Tuple]]:
        """ Downloads csv.gz file and returns the contained query results.

        s3_file_name (str): Name of the gzipped csv file with the query results.
        delimiter (str): Delimiter to be used for csv output file.

        Returns:
            A (list, list) tuple where the first element is the columns and the second element is
                the rows returned by the select query.
        """
        object_key = os.path.join(s3_dir_key, s3_file_name)
        s3_object = get_object(bucket_name=s3_bucket, key=object_key)
        decompressed_object = gzip.decompress(s3_object)
        decompressed_buffer = io.BytesIO(decompressed_object)
        # Decode utf-8 string and read csv columns and rows
        with io.TextIOWrapper(decompressed_buffer, encoding='utf-8') as wrapper:
            csv_reader = csv.reader(wrapper, delimiter=delimiter, lineterminator='\n',
                                    quoting=csv.QUOTE_NONNUMERIC)
            columns = next(csv_reader)
            rows = cls.cast_query_result_types(columns, csv_reader)
        return columns, rows

    @classmethod
    def cast_query_result_types(cls, columns: Iterable, row_iterable: Iterable):
        return [ResponseRecord.transform(columns, row) for row in row_iterable]

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.conn.close()

    def __del__(self):
        self.conn.close()
