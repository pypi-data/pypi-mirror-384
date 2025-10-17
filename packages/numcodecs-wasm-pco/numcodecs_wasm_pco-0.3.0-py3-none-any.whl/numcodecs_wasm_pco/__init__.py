__all__ = ["Pco"]

import importlib.resources
import sys

from numcodecs_wasm import WasmCodecMeta


class Pco(
    metaclass=WasmCodecMeta,
    wasm=importlib.resources.files(
        sys.modules[__name__]
    ).joinpath("codec.wasm").read_bytes(),
):
    pass
