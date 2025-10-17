__all__ = ["Jpeg2000"]

import importlib.resources
import sys

from numcodecs_wasm import WasmCodecMeta


class Jpeg2000(
    metaclass=WasmCodecMeta,
    wasm=importlib.resources.files(
        sys.modules[__name__]
    ).joinpath("codec.wasm").read_bytes(),
):
    pass
