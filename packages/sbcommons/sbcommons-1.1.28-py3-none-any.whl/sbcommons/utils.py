import ast
import datetime as dt
import logging
from functools import reduce
from string import Template
import re
from typing import List, Any
import sbcommons.aws.s3 as s3

logger = logging.getLogger(__name__)


def evaluate_recursively(obj, logger: logging.Logger = None):
    """ Evaluates a python object recursively.

        Example:
            "{'give_away': {'amount': 500}}"
            returns
            {give_away': {'amount': 500}}

        Args:
            obj: Any python object
            logger: Object for logging.

        Return:
            The actual evaluated python object down to the root element.
    """
    try:
        if isinstance(obj, list):
            data = [evaluate_recursively(el, logger) for el in obj]
        elif isinstance(obj, dict):
            data = obj
            for k, v in data.items():
                data[k] = evaluate_recursively(v, logger)
        elif isinstance(obj, tuple):
            data = (evaluate_recursively(el, logger) for el in obj)
        elif isinstance(obj, (int, bool, float)):
            return obj
        else:
            data = ast.literal_eval(obj)
            if isinstance(data, (list, dict, tuple)):
                data = evaluate_recursively(data)
        return data
    except (ValueError, SyntaxError) as e:
        # If we got a Value error try adding quotes to the object in case it is a string
        if isinstance(e, ValueError):
            try:
                data = ast.literal_eval("'" + obj + "'")
                return data
            except SyntaxError:
                pass
        # If adding quotes did not help then log a warning but return object as is
        if logger:
            logger.warning(f"Warning: object could not be parsed: {repr(e)}")
        return obj


def get_field_from_included(data_list, included_list, field_path):
    field_name = field_path.split('.')[-1]
    for data_dict_idx, data_dict in enumerate(data_list):
        for included_dict in included_list:
            # fetch the value if the kaviyo ids match
            if data_dict['relationships']['profile']['data']['id'] == included_dict['id']:
                result = rget(included_dict, field_path)
                if result:
                    data_list[data_dict_idx][field_name] = result
                break
    return data_list


def get_value_from_path(data: dict, path: str):
    """ Helper function to get nested field from dictionary.
    Args:
        data: The dictionary with the data at hand.
        path: The path inside the dictionary that we want to access. Each field is sperated by ".".
        """
    if not isinstance(data, dict):
        raise TypeError(f"parameter data is of type {type(data)} instead of dict")
    keys = path.split(".")
    result = data
    try:
        for key in keys:
            result = result[key]
        return result
    except KeyError:
        return None


def rget(obj, path):
    return reduce(lambda d, key: d.get(key) if d else None, path.split('.'), obj)


def remove_email_info_from_text(text: str):
    """ Given some text we remove any email information and replace it with *
    Parameters:
        text: The text for which we want to remove email information """

    email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    return re.sub(pattern=email_pattern,
                  repl='*****',
                  string=text)


def chunk_list(x: List[Any], n: int):
    """Yield successive n-sized chunks from x."""
    for i in range(0, len(x), n):
        yield x[i:i + n]


def validate_email(email: str):
    match = re.match(r'^\b[A-Za-z0-9._%+-]+@[A-Za-z0-9]+[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b$', email)
    if not match:
        logger.info(f'Filtering out {email} from update data as the email is invalid')
    return match


def get_date_string() -> str:
    """ Returns date string in a DD_MM_YYYY format according to UTC time."""
    now = dt.datetime.now(dt.timezone.utc)
    datetime_string_template = Template(
        "${day}_${month}_${year}")
    return datetime_string_template.substitute(
        day=now.day,
        month=now.month,
        year=now.year
    )


def clear_s3_path(s3_bucket: str, s3_key: str, backup_bucket: str):
    """ Clears objects in S3 path specified by <s3_bucket> and <s3_key>. """
    s3_objects = s3.list_objects(bucket_name=s3_bucket,
                                 path=s3_key,
                                 return_object_keys=True)
    s3_objects_dict = {key: key for key in s3_objects}

    s3.copy_objects(source_bucket_name=s3_bucket,
                    destination_bucket_name=backup_bucket,
                    keys=s3_objects_dict)

    for s3_key in s3_objects:
        s3.delete_object(bucket_name=s3_bucket, key=s3_key)
