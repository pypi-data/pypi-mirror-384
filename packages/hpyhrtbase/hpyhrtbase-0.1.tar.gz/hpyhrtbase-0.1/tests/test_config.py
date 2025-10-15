import os

from hpyhrtbase.config import Params, params_from_file


def test_params_from_file(configs_dir):
    config_path = os.path.join(configs_dir, "example_config_001.conf")
    params = params_from_file(config_path)

    assert params.key1 == "value1"
    assert params.key2 == "value2"
    assert params.key_dict.inner_key1 == "inner_value1"


def test_params_to_dict():
    inner_params = Params(inner_key1="inner_value1")
    params = Params(key1="value1", key2="value2")
    params["key_dict"] = inner_params

    assert params.key1 == "value1"
    assert params.key2 == "value2"
    assert params.key_dict.inner_key1 == "inner_value1"

    params_dict = params.as_dict()

    assert params_dict["key1"] == "value1"
    assert params_dict["key2"] == "value2"
    assert params_dict["key_dict"]["inner_key1"] == "inner_value1"
