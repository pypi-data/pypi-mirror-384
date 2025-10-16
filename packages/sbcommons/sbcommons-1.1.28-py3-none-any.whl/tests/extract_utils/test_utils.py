import unittest
import sbcommons.extract_utils.utils as utils


def test_create_md5_hash():
    # Test case 1: Known string and its SHA-256 hash
    input_str = "hello"
    expected_hash = "5d41402abc4b2a76b9719d911017c592"
    assert utils.create_md5_hash(input_str) == expected_hash, "Create md5 for 'hello' failed"

    # Test case 2: Empty string
    input_str = ""
    expected_hash = "d41d8cd98f00b204e9800998ecf8427e"
    assert utils.create_md5_hash(input_str) == expected_hash, "Create md5 for blank string failed"


def test_create_md5_hash_uniqueness():
    input_str = "A B"*1000
    assert utils.create_md5_hash(input_str) == utils.create_md5_hash(input_str), "Create_hash function uniqueness failed"


def test_json_object_to_list():
    input_json = {
        "subject": "Test Subject",
        "messages": [
            {"message": "Message 1"},
            {"message": "Message 2"}
        ]
    }
    expected_output = [
        {
            "subject": "Test Subject",
            "json_data": {"message": "Message 1"},
            "event_id": utils.create_md5_hash(str({"message": "Message 1"}))
        },
        {
            "subject": "Test Subject",
            "json_data": {"message": "Message 2"},
            "event_id": utils.create_md5_hash(str({"message": "Message 2"}))
        }
    ]
    result = utils.json_object_to_list(input_json)
    assert result == expected_output, "Converting json object to json list with default subject and record failed"


def test_empty_json_object_to_list():
    input_json = {
        "subject": "Test Subject",
        "messages": []
    }
    expected_output = []
    result = utils.json_object_to_list(input_json)
    assert result == expected_output, "Converting empty jason object to list failed"


def test_json_object_to_list_with_keys():
    # Try json_object_to_list with different keys
    input_json = {
        "topic": "Different Subject",
        "entries": [
            {"data": "Entry 1"},
            {"data": "Entry 2"}
        ]
    }
    expected_output = [
        {
            "subject": "Different Subject",
            "json_data": {"data": "Entry 1"},
            "event_id": utils.create_md5_hash(str({"data": "Entry 1"}))
        },
        {
            "subject": "Different Subject",
            "json_data": {"data": "Entry 2"},
            "event_id": utils.create_md5_hash(str({"data": "Entry 2"}))
        }
    ]
    result = utils.json_object_to_list(input_json, subject_key='topic', record_key='entries')
    assert result == expected_output, "Converting json object to list with different keys failed"
