__all__ = ["Round"]

import importlib.resources
import sys

from numcodecs_wasm import WasmCodecMeta


class Round(
    metaclass=WasmCodecMeta,
    wasm=importlib.resources.files(
        sys.modules[__name__]
    ).joinpath("codec.wasm").read_bytes(),
):
    pass
