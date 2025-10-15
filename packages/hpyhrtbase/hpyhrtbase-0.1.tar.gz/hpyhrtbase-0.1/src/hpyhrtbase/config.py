from __future__ import annotations

import json
import logging
import os
import types
from collections.abc import Iterable
from typing import Any, cast

import pyhocon

logging.basicConfig(format='%(asctime)s  %(levelname)-8s [%(name)s] %(module)s:%(funcName)s:%(lineno)d: %(message)s',
                level=logging.INFO)


class Params:
    """Params handler object.

    This functions as a nested dict, but allows for seamless dot-style access, similar to tf.HParams but without the type validation. For example:

    p = Params(name="model", num_layers=4)
    p.name  # "model"
    p['data'] = Params(path="file.txt")
    p.data.path  # "file.txt"
    """

    @staticmethod
    def clone(source: Any, strict: bool = True) -> Params | None:
        if isinstance(source, pyhocon.ConfigTree):
            return Params(**source.as_plain_ordered_dict())
        elif isinstance(source, Params):
            return Params(**source.as_dict())
        elif isinstance(source, dict):
            return Params(**source)
        elif strict:
            raise ValueError("Cannot clone from type: " + str(type(source)))
        else:
            return None

    def __getattr__(self, name: str) -> Any:
        raise AttributeError(f"{name} not found")

    def __setattr__(self, name: str, value: Any) -> None:
        super().__setattr__(name, value)

    def __getitem__(self, k: str) -> Any:
        return getattr(self, k)

    def __contains__(self, k: str) -> bool:
        return k in self._known_keys

    def __setitem__(self, k: str, v: Any) -> None:
        assert isinstance(k, str)
        if isinstance(self.get(k, None), types.FunctionType):
            raise ValueError(f"Invalid parameter name (overrides reserved name '{k}').")

        converted_val = Params.clone(v, strict=False)

        if converted_val is not None:
            setattr(self, k, converted_val)
        else:  # plain old data
            setattr(self, k, v)

        self._known_keys.add(k)

    def __delitem__(self, k: str) -> None:
        if k not in self:
            raise ValueError(f"Parameter {k} not found.")
        delattr(self, k)
        self._known_keys.remove(k)

    def __init__(self, **kw: Any) -> None:
        """Create from a list of key-value pairs."""
        self._known_keys: set[str] = set()
        for k, v in kw.items():
            self[k] = v

    def get(self, k: str, default: Any = None) -> Any:
        return getattr(self, k, default)

    def keys(self) -> list[str]:
        return sorted(self._known_keys)

    def as_dict(self) -> dict[str, Any]:
        """Recursively convert to a plain dict."""
        def convert(v: Any) -> Any:
            return v.as_dict() if isinstance(v, Params) else v
        return {k: convert(self[k]) for k in self.keys()}

    def __repr__(self) -> str:
        return self.as_dict().__repr__()

    def __str__(self) -> str:
        return json.dumps(self.as_dict(), indent=2, sort_keys=True)


# Argument handling is as follows:
# 1) read config file into pyhocon.ConfigTree
# 2) merge overrides into the ConfigTree
# 3) validate specific parameters with custom logic


def params_from_file(config_files: str | Iterable[str],
                     overrides: str | None = None) -> Params:
    config_string = ''

    if isinstance(config_files, str):
        config_files = [config_files]

    for config_file in config_files:
        with open(config_file, encoding='utf-8') as fd:
            print("")
            logging.info(f"Loading config from {config_file}")
            config_string += fd.read()
            config_string += '\n'

    if overrides:
        logging.info(f"Config overrides: {overrides}")
        # Append overrides to file to allow for references and injection.
        config_string += "\n"
        config_string += overrides

    basedir = os.path.dirname(config_file)  # directory context for includes
    config = pyhocon.ConfigFactory.parse_string(config_string, basedir=basedir)
    return cast(Params, Params.clone(config))
