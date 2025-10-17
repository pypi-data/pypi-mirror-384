__all__ = ["Tthresh"]

import importlib.resources
import sys

from numcodecs_wasm import WasmCodecMeta


class Tthresh(
    metaclass=WasmCodecMeta,
    wasm=importlib.resources.files(
        sys.modules[__name__]
    ).joinpath("codec.wasm").read_bytes(),
):
    pass
