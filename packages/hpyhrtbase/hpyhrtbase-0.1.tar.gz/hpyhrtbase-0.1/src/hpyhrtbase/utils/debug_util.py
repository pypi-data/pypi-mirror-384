class DebugUtil:
    @staticmethod
    def reset_app() -> None:
        from hpyhrtbase import init_app_base

        init_app_base._init_app_base_done = False
        init_app_base._logging_setup_done = False
