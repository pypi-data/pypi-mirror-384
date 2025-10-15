import hashlib
import random
import uuid


class RandomUtil:
    @staticmethod
    def gen_guid() -> str:
        return str(uuid.uuid4())

    @staticmethod
    def hash_sha1(input_str: str, private: str | None = None) -> str:
        if not private:
            private = "Work hard, study hard, play hard, enjoy the life"
        m = hashlib.sha1()
        m.update(private.encode())
        m.update(input_str.encode())
        m.update(private.encode())
        digest = m.hexdigest()
        return digest

    @staticmethod
    def is_valid_uuid(uuid_to_test: str, version: int = 4) -> bool:
        try:
            uuid_obj = uuid.UUID(uuid_to_test, version=version)
        except ValueError:
            return False

        return str(uuid_obj) == uuid_to_test

    @staticmethod
    def random_num_seq(seq_len: int) -> str:
        result = ""
        for i in range(seq_len):
            result += "%d" % random.randint(0, 9)
        return result
