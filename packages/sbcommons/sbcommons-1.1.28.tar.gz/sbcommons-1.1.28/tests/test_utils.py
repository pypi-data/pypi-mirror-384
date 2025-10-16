from sbcommons import utils


def test_get_value_from_path():
    input_json = {
            "a": {
                "b": {
                    "c": "value_c",
                    "d": 10
                },
                "e": "value_e"
            },
            "f": {
                "g": {
                    "h": [1, 2, 3]
                }
            }
        }
    assert utils.get_value_from_path(input_json, "a.b.c") == "value_c"
    assert utils.get_value_from_path(input_json, "a.b.d") == 10
    assert utils.get_value_from_path(input_json, "a.e") == "value_e"
    assert utils.get_value_from_path(input_json, "f.g.h") == [1, 2, 3]
