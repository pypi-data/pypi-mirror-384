import hashlib


def convert_keys_to_lowercase(data: dict) -> dict:
    """
    Recursively converts all keys in a dictionary to lowercase.
    """
    if isinstance(data, dict):
        return {k.lower(): convert_keys_to_lowercase(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [convert_keys_to_lowercase(item) for item in data]
    else:
        return data


def create_md5_hash(input_str: str) -> str:
    """
    Returns: md5 hash of the input string
    """
    encoded_str = input_str.encode()
    hash_object = hashlib.md5(encoded_str)
    hash_hex = hash_object.hexdigest()
    return hash_hex


def json_object_to_list(input_json: dict, subject_key='subject', record_key='messages') -> list[dict]:
    """
    Convert Json object into a list of json records plus adding subject and unique event_id to each data record

    Parameters:
    input_json (json object): The Json object to convert with this format
        {
            "subject_key": "subject",
            "record_key": [
                json_record1,
                json_record2,
                ...
            ]
        }
    subject_key (str): The key to the subject field in input_json
    record_key (str): The key to the records list in input_json

    Returns:
    A list of json_records with subject and a generated event_id(unique to every json_record) [{subject: subject, json_data: json_record, event_id: hash_of_json_record}, ...]
    """
    json_record_list = [dict(subject=input_json[subject_key], json_data=record, event_id=create_md5_hash(str(record))) for record
                   in input_json[record_key]]
    return json_record_list
