import types
from typing import Any

SAFE_PRIMITIVE_TYPES = {str, int, float, bool, bytes} # TODO: deal with bytes

SAFE_PRIMITIVE_TYPES_OR_NONE = SAFE_PRIMITIVE_TYPES | {types.NoneType}


class TSRaw:
  def __init__(self, value: Any):
    self.value: Any = value


class TSEnum:
  def __init__(self, name: str, value: str):
    self.name: str = name
    self.value: str = value


class TSUndefined:
  pass
