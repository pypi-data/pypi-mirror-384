from hpyhrtbase import log
from hpyhrtbase.config import Params


def test_setup_logging(tmp_path):
    params = Params()
    params.project_dir = str(tmp_path)

    app_log_path = tmp_path / "logs" / "app.log"

    log.setup_logging(params)

    log_content = app_log_path.read_text(encoding="utf-8")
    assert "info: App start logging" in log_content
