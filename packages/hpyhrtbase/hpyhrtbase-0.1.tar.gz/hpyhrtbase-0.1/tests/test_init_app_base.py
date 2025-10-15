import os

from hpyhrtbase import hpyhrt_context, init_app_base


def test_init_app_base(configs_dir):
    config_path = os.path.join(configs_dir, "default_config.conf")
    init_app_base.init_app_base(config_path, check_dir_names=["configs"])

    config_inst = hpyhrt_context.get_config_inst()

    assert config_inst.key1 == "value1"
