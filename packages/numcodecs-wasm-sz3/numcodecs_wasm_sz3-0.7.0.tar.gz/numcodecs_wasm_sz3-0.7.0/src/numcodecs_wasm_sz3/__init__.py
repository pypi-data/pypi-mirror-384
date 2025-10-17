__all__ = ["Sz3"]

import importlib.resources
import sys

from numcodecs_wasm import WasmCodecMeta


class Sz3(
    metaclass=WasmCodecMeta,
    wasm=importlib.resources.files(
        sys.modules[__name__]
    ).joinpath("codec.wasm").read_bytes(),
):
    pass
