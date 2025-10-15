import os

from hpyhrtbase import hpyhrt_context
from hpyhrtbase.config import params_from_file


def test_global_context():
    global_context = hpyhrt_context.get_global_context()
    global_context.key1 = "value1"


def test_config_inst(configs_dir):
    config_path = os.path.join(configs_dir, "example_config_001.conf")
    params = params_from_file(config_path)

    hpyhrt_context.set_config_inst(params)

    config_inst = hpyhrt_context.get_config_inst()

    assert config_inst.key1 == "value1"
