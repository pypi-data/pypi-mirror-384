import types
import typing
from datetime import datetime
from typing import TypeAliasType

from pydantic.types import AwareDatetime

from alxhttp.typescript.type_checks import extract_class, get_literals, is_alias, is_annotated, is_dict, is_list, is_literal, is_model_type, is_tuple, is_type_or_alias, is_union
from alxhttp.typescript.types import SAFE_PRIMITIVE_TYPES, TSEnum, TSRaw, TSUndefined


def pytype_to_tstype(t: type | TypeAliasType, self_type: type | TypeAliasType | None = None) -> str:
  if t == typing.Self:
    if self_type is None:
      raise ValueError('Self type is required')
    return pytype_to_tstype(self_type)
  elif is_type_or_alias(t, str):
    return 'string'
  elif is_type_or_alias(t, bytes):
    return 'string' # TODO: deal with bytes
  elif is_type_or_alias(t, bool):
    return 'boolean'
  elif is_type_or_alias(t, int) or is_type_or_alias(t, float):
    return 'number'
  elif is_type_or_alias(t, datetime) or is_type_or_alias(t, AwareDatetime):
    return 'Date'
  elif is_type_or_alias(t, types.NoneType):
    return 'null'
  elif is_type_or_alias(t, TSUndefined):
    return 'undefined'
  elif is_type_or_alias(t, typing.Any):
    return 'any'
  elif is_literal(t):
    literal_values = get_literals(t)
    literal_str_values = [f"'{x}'" if isinstance(x, str) else str(x) for x in literal_values]
    return '|'.join(literal_str_values)
  elif is_alias(t):
    return pytype_to_tstype(t.__value__, self_type=self_type)
  elif is_annotated(t):
    targs = typing.get_args(t)
    if targs[0] in SAFE_PRIMITIVE_TYPES:
      if isinstance(targs[1], TSRaw):
        if isinstance(targs[1].value, str):
          return f"'{targs[1].value}'"
        else:
          return str(targs[1].value)
      elif isinstance(targs[1], TSEnum):
        return f'{targs[1].name}.{targs[1].value}'
      else:
        return pytype_to_tstype(targs[0], self_type=self_type)
    else:
      return pytype_to_tstype(targs[0], self_type=self_type)
  elif is_union(t):
    targs = typing.get_args(t)
    return ' | '.join(sorted([pytype_to_tstype(targ, self_type=self_type) for targ in targs]))
  elif is_list(t):
    return f'({pytype_to_tstype(typing.get_args(t)[0], self_type=self_type)})[]'
  elif is_tuple(t):
    return f'[{",".join([pytype_to_tstype(a, self_type=self_type) for a in typing.get_args(t)])}]'
  elif is_dict(t):
    k_type, v_type = typing.get_args(t)
    return f'Record<{pytype_to_tstype(k_type, self_type=self_type)}, {pytype_to_tstype(v_type, self_type=self_type)}>'
  elif is_model_type(t):
    return extract_class(t)
  else:
    raise ValueError
