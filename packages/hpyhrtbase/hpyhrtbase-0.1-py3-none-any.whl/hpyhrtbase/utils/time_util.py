import time
from collections.abc import Generator
from contextlib import contextmanager
from datetime import date, datetime
from types import SimpleNamespace


class TimeUtil:
    @staticmethod
    def convert_date_int_to_date_obj(date_int: int) -> date:
        date_obj = date(date_int//10000, (date_int//100)%100, date_int%100)
        return date_obj

    @staticmethod
    def convert_date_obj_to_date_int(date_obj: date) -> int:
        date_int = date_obj.year * 10000 + date_obj.month * 100 + date_obj.day
        return date_int

    @staticmethod
    def datetime_fromisoformat(datetime_str: datetime | str) -> datetime | None:
        try:
            if isinstance(datetime_str, datetime):
                return datetime_str

            if datetime_str[-1] == "Z":
                datetime_str = datetime_str[:-1] + "+00:00"

            parsed_datetime = datetime.fromisoformat(datetime_str)
        except Exception:
            return None
        return parsed_datetime

    @staticmethod
    def get_current_time_isoformat() -> str:
        local_datetime = datetime.now()
        return local_datetime.isoformat()

    @staticmethod
    def get_current_time_ms() -> int:
        millis = int(round(time.time() * 1000))
        return millis

    @staticmethod
    def get_current_time_monotonic() -> float:
        return time.monotonic()

    @contextmanager
    @staticmethod
    def timeit() -> Generator[SimpleNamespace]:
        start_time = time.monotonic()
        ns = SimpleNamespace()
        yield ns
        duration = time.monotonic() - start_time
        ns.duration = duration


if __name__ == "__main__":
    print(TimeUtil.get_current_time_isoformat())
