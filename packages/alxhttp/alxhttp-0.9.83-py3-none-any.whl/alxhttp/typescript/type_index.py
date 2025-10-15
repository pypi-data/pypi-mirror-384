import typing
from collections import defaultdict
from collections.abc import Generator
from dataclasses import dataclass, field
from datetime import datetime
from types import NoneType
from typing import Any, TypeAliasType, get_type_hints

import pydantic
from pydantic import BaseModel, HttpUrl
from pydantic.types import AwareDatetime

from alxhttp.pydantic.route import RouteDetails
from alxhttp.typescript.basic_syntax import braces
from alxhttp.typescript.syntax_tree import ObjectInit, ObjectInitField, ObjectType, ObjectTypeField, TypeDecl, UnionType
from alxhttp.typescript.type_checks import (
  extract_class,
  get_literal,
  is_alias,
  is_annotated,
  is_class_var,
  is_class_var_or_annotated_class_var,
  is_dict,
  is_generic_type,
  is_list,
  is_literal,
  is_model_type,
  is_optional,
  is_safe_primitive_type_or_union,
  is_tuple,
  is_type_or_annotated_type,
  is_union,
  is_union_of_models,
  is_union_of_safe_primitive_types_or_none,
)
from alxhttp.typescript.type_conversion import pytype_to_tstype
from alxhttp.typescript.types import SAFE_PRIMITIVE_TYPES, TSEnum, TSUndefined


class PydanticError(BaseModel):
  type: str
  loc: list[str]
  msg: str
  input: str
  ctx: dict[str, str]


class PydanticErrorResp(BaseModel):
  errors: list[PydanticError]


def should_skip_field(field_name: str, field_type: type | TypeAliasType) -> bool:
  if is_class_var_or_annotated_class_var(field_type):
    return True
  elif field_type == pydantic.ConfigDict:
    return True
  elif field_name.startswith('_'):
    return True
  elif is_annotated(field_type) and typing.get_args(field_type)[0] == pydantic.ConfigDict:
    return True
  return False


def model_to_type(name: str, model: Any) -> ObjectType:
  model_fields = get_type_hints(model, include_extras=True)
  fields: list[ObjectTypeField] = []
  for field_name, field_type in model_fields.items():
    if should_skip_field(field_name, field_type):
      continue
    td = TypeDecl(field_type, self_type=model)
    fields.append(ObjectTypeField(field_name, td, None))

  return ObjectType(name, fields)


def _get_arg_list(t: type | TypeAliasType) -> list[type | TypeAliasType]:
  args = typing.get_args(t)
  return list(args)


def nullable_union_of_toplevel_fields(name: str, models: list[Any]) -> ObjectType:
  fields: list[ObjectTypeField] = []
  for model in models:
    model_fields = get_type_hints(model, include_extras=True)

    for field_name, field_type in model_fields.items():
      if should_skip_field(field_name, field_type):
        continue
      if not is_optional(field_type):
        field_type = field_type | None | TSUndefined
      fields.append(ObjectTypeField(field_name, TypeDecl(field_type, self_type=model), None))

  return ObjectType(name, fields, export=False)


def jsdoc_of_toplevel_fields(models: list[Any]) -> list[str]:
  fields: list[ObjectTypeField] = []
  for model in models:
    model_fields = get_type_hints(model, include_extras=True)

    for field_name, field_type in model_fields.items():
      if should_skip_field(field_name, field_type):
        continue
      fields.append(ObjectTypeField(field_name, TypeDecl(field_type, self_type=model), None))

  return [f'@param {{{f.decl}}} {f.name}' for f in fields]


def extract_enum_references(enum: dict[str, set[str]], model: Any) -> None:
  model_fields = get_type_hints(model, include_extras=True)
  for field_name, field_type in model_fields.items():
    if should_skip_field(field_name, field_type):
      continue
    if is_annotated(field_type):
      targs = typing.get_args(field_type)
      if isinstance(targs[1], TSEnum):
        enum[targs[1].name].add(targs[1].value)


def gen_wire_func(name: str, ret_type: str, object_init: ObjectInit):
  return f'export function {name}(root: any): {ret_type} {{ return {object_init} }};\n'


def recurse_model_types(t: type | TypeAliasType, seen: set[type | TypeAliasType] | None = None) -> Generator[type | TypeAliasType, None, None]:
  if seen is None:
    seen = set()

  if t in seen:
    return
  seen.add(t)

  if should_skip_field('', t):
    return

  if is_alias(t):
    if is_union_of_models(t.__value__):
      yield t
    yield from recurse_model_types(t.__value__, seen)

  if is_generic_type(t):
    for arg in typing.get_args(t):
      yield from recurse_model_types(arg, seen)
  elif is_model_type(t):
    yield t

    try:
      for base in t.mro():
        if base in seen:
          continue
        s = str(base)
        if base is object or 'pydantic.main.BaseModel' in s or 'alxhttp.pydantic.basemodel.BaseModel' in s:
          continue
        yield from recurse_model_types(base, seen)
    except Exception:
      pass

    model_fields = get_type_hints(t)
    for field_name, field_type in model_fields.items():
      if should_skip_field(field_name, field_type):
        continue
      yield from recurse_model_types(field_type, seen)


def _first_real_field(subtype: type | TypeAliasType) -> tuple[str, type | TypeAliasType]:
  model_fields = get_type_hints(subtype)
  for first_name, field_type in model_fields.items():
    if should_skip_field(first_name, field_type):
      continue
    return first_name, field_type
  assert False


def _discrimination_expr(src_name: str, type_args: list[type | TypeAliasType]) -> str:
  discrimination_expr = ''
  first_first_name = None
  finished = False
  for n, subtype in enumerate(type_args):
    first_name, first_field_type = _first_real_field(subtype)
    if not first_first_name:
      first_first_name = first_name
    assert first_name == first_first_name  # simplifying assumption: all subtypes will have a common first literal key
    if is_literal(first_field_type):
      literal_value = get_literal(first_field_type)
      if isinstance(literal_value, str):
        literal_value = f"'{literal_value}'"

      discrimination_expr += f'({src_name}.{first_name} === {literal_value}) ? get{pytype_to_tstype(subtype)}FromWire({src_name}) : '
    elif n == len(type_args) - 1:
      finished = True
      discrimination_expr += f'get{pytype_to_tstype(subtype)}FromWire({src_name})'

  if not finished:
    discrimination_expr += ' unreachable()'
  return discrimination_expr


@dataclass
class TypeIndex:
  py_to_ts: dict[type | TypeAliasType, ObjectType] = field(default_factory=dict)
  ts_to_py: dict[str, type | TypeAliasType] = field(default_factory=dict)

  py_to_wire_func: dict[type | TypeAliasType, str] = field(default_factory=dict)
  py_to_wire_func_name: dict[type | TypeAliasType, str] = field(default_factory=dict)

  serialize_wire_func: dict[type | TypeAliasType, str] = field(default_factory=dict)
  serialize_wire_func_name: dict[type | TypeAliasType, str] = field(default_factory=dict)

  py_to_ts_union: dict[type | TypeAliasType, UnionType] = field(default_factory=dict)

  enum_refs: defaultdict[str, set[str]] = field(default_factory=lambda: defaultdict(set))

  def gen_enum_defs(self) -> str:
    tdefs: list[str] = []
    for ename, evals in self.enum_refs.items():
      tdefs.append(f'enum {ename} {braces([f"{ev} = '{ev}'" for ev in sorted(evals)], sep=",")};')
    return '\n\n'.join(tdefs) + '\n\n'

  def body_and_match_field_names(self, rd: RouteDetails[Any]) -> list[str]:
    body_arg_names = [x.name for x in self.py_to_ts[rd.body].fields]
    match_info_arg_names = [x.name for x in self.py_to_ts[rd.match_info].fields]
    return match_info_arg_names + body_arg_names

  def recurse_model(self, mt: type, init_from_wire: bool = True, init_to_wire: bool = True) -> None:
    for m in recurse_model_types(mt):
      if should_skip_field('', m):
        continue
      elif is_alias(m) and is_union_of_models(m.__value__):
        type_name = str(m)
        union_type = m.__value__
        self.py_to_ts_union[union_type] = UnionType(type_name, members=[extract_class(c) for c in typing.get_args(union_type)], export=True)
        if init_from_wire:
          self.init_discriminated_union_from_wire(union_type)
      else:
        ts_name = extract_class(m)
        t = model_to_type(ts_name, m)
        extract_enum_references(self.enum_refs, m)
        self.py_to_ts[m] = t
        self.ts_to_py[ts_name] = m

        if init_from_wire:
          self.init_from_wire(m)
        if init_to_wire:
          self.init_to_wire(m)

  def _gen_init_field_assignment(self, type: type | TypeAliasType, src_name: str = 'root', depth: int = 0, self_type: type | TypeAliasType | None = None) -> str | None:
    depth += 1

    kn = f'k{depth}'
    vn = f'v{depth}'

    type_args = _get_arg_list(type)

    if is_annotated(type):
      return self._gen_init_field_assignment(type_args[0], src_name, depth, self_type)
    elif type in SAFE_PRIMITIVE_TYPES:
      return src_name
    elif type == HttpUrl:
      return src_name
    elif is_literal(type):
      return src_name
    elif type == datetime or type == AwareDatetime:  # pyright: ignore[reportUnnecessaryComparison]
      return f'new Date({src_name} * 1000)'
    elif type == Any:
      return src_name
    elif type == NoneType:
      return src_name
    elif is_class_var(type):
      return None
    elif is_alias(type):
      return self._gen_init_field_assignment(type.__value__, src_name, depth, self_type)
    elif is_list(type) or is_tuple(type):
      if is_safe_primitive_type_or_union(type_args[0]):
        # Small optimization
        return src_name

      return f'{src_name}.map(({vn}: {pytype_to_tstype(type_args[0], self_type=self_type)}) => {{ return {self._gen_init_field_assignment(type_args[0], vn, depth, self_type)} }})'
    elif is_union_of_safe_primitive_types_or_none(type):
      return src_name
    elif is_optional(type):
      sub = self._gen_init_field_assignment(type_args[0], src_name, depth, self_type)
      if sub is None:
        return None
      return f'({src_name} === null) ? null : ' + sub
    elif is_union_of_models(type):
      return _discrimination_expr(src_name, type_args)
    elif is_union(type):
      # This case represents a complex union i.e "str | datetime"
      assert False
    elif is_dict(type):
      assert is_type_or_annotated_type(type_args[0], str)
      ktype = pytype_to_tstype(type_args[0])
      vtype = pytype_to_tstype(type_args[1])
      return (
        f'Object.fromEntries(Object.entries({src_name} as Record<{ktype}, {vtype}>).map(([{kn}, {vn}]) => {{ return [{kn}, {self._gen_init_field_assignment(type_args[1], vn, depth, self_type)}] }} ))'
      )
    elif is_model_type(type):
      return f'get{pytype_to_tstype(type)}FromWire({src_name})'
    elif type == typing.Self:
      assert self_type is not None
      return self._gen_init_field_assignment(self_type, src_name, depth, self_type)
    else:
      raise ValueError

  def _gen_uninit_field_assignment(self, type: type | TypeAliasType, src_name: str = 'root', depth: int = 0, self_type: type | TypeAliasType | None = None) -> str | None:
    depth += 1

    kn = f'k{depth}'
    vn = f'v{depth}'

    type_args = typing.get_args(type)

    if is_annotated(type):
      return self._gen_uninit_field_assignment(type_args[0], src_name, depth, self_type)
    elif type in SAFE_PRIMITIVE_TYPES:
      return src_name
    elif is_literal(type):
      return src_name
    elif type == NoneType:
      return src_name
    elif type == datetime or type == AwareDatetime:  # pyright: ignore[reportUnnecessaryComparison]
      return f'{src_name}.getTime()'
    elif type == Any:
      return src_name
    elif should_skip_field('', type):
      return None
    elif type == typing.Self:
      assert self_type is not None
      return self._gen_uninit_field_assignment(self_type, src_name, depth, self_type)
    elif is_alias(type):
      return self._gen_uninit_field_assignment(type.__value__, src_name, depth, self_type)
    elif is_list(type) or is_tuple(type):
      # TODO: ignoring tuple types
      return f'{src_name}.map(({vn}: {pytype_to_tstype(type_args[0], self_type=self_type)}) => {{ return {self._gen_uninit_field_assignment(type_args[0], vn, depth, self_type)} }})'
    elif is_union_of_safe_primitive_types_or_none(type):
      return src_name
    elif is_optional(type):
      sub = self._gen_uninit_field_assignment(type_args[0], src_name, depth, self_type)
      if sub is None:
        return None
      return f'({src_name} === null) ? null : ' + sub
    elif is_union_of_models(type):
      discrimination_expr = ''
      first_first_name = None
      finished = False
      for n, subtype in enumerate(type_args):
        first_name, first_field_type = list(get_type_hints(subtype).items())[0]
        if not first_first_name:
          first_first_name = first_name
        assert first_name == first_first_name  # simplifying assumption: all subtypes will have a common first literal key
        if is_literal(first_field_type):
          literal_value = get_literal(first_field_type)
          if isinstance(literal_value, str):
            literal_value = f"'{literal_value}'"

          discrimination_expr += f'({src_name}.{first_name} === {literal_value}) ? convert{pytype_to_tstype(subtype, self_type=self_type)}ToWire({src_name}) : '
        elif n == len(type_args) - 1:
          finished = True
          discrimination_expr += f'convert{pytype_to_tstype(subtype, self_type=self_type)}ToWire({src_name})'

      if not finished:
        discrimination_expr += ' unreachable()'
      return discrimination_expr
    elif is_union(type):
      # This case represents a complex union i.e "str | datetime"
      assert False
    elif is_dict(type):
      assert is_type_or_annotated_type(type_args[0], str)
      ktype = pytype_to_tstype(type_args[0])
      vtype = pytype_to_tstype(type_args[1])
      sub = self._gen_uninit_field_assignment(type_args[1], vn, depth, self_type)
      if sub is None:
        return None
      return f'Object.fromEntries(Object.entries({src_name} as Record<{ktype}, {vtype}>).map(([{kn}, {vn}]) => {{ return [{kn}, {sub}] }} ))'

    elif is_model_type(type):
      return f'convert{pytype_to_tstype(type, self_type=self_type)}ToWire({src_name})'
    else:
      raise ValueError

  def init_discriminated_union_from_wire(self, py_type: type, wire_arg: str = 'root') -> str:
    ts_type = self.py_to_ts_union[py_type]
    de = _discrimination_expr(wire_arg, _get_arg_list(py_type))

    wire_func_name = f'get{ts_type.name}FromWire'
    wire_func = f'export function {wire_func_name}(root: any): {ts_type.name} {{ return {de} }};\n'

    self.py_to_wire_func_name[py_type] = wire_func_name
    self.py_to_wire_func[py_type] = wire_func

    return wire_func

  def init_from_wire(self, py_type: type | TypeAliasType, wire_arg: str = 'root') -> str:
    """
    Inits a new JS object based on one that came via json over the wire. Allows
    us to do things like turn float timestamps into js Date objects.
    """
    ts_type = self.py_to_ts[py_type]
    field_assignments: list[ObjectInitField] = []
    for tsfield in ts_type.fields:
      assert not isinstance(tsfield.decl.decl, str)
      field_type = self._gen_init_field_assignment(tsfield.decl.decl, f'{wire_arg}.{tsfield.name}', depth=0, self_type=py_type)
      if field_type is None:
        continue
      field_assignments.append(
        ObjectInitField(
          tsfield.name,
          field_type,
        )
      )

    object_init = ObjectInit(field_assignments)
    wire_func_name = f'get{ts_type.name}FromWire'
    wire_func = gen_wire_func(wire_func_name, ts_type.name, object_init)

    self.py_to_wire_func_name[py_type] = wire_func_name
    self.py_to_wire_func[py_type] = wire_func

    return wire_func

  def init_to_wire(self, py_type: type | TypeAliasType, wire_arg: str = 'root') -> str:
    """
    Inits a new JS object to be sent over the wire. Allows
    us to do things like turn js Date objects into float timestamps.
    """
    ts_type = self.py_to_ts[py_type]
    field_assignments: list[ObjectInitField] = []
    for tsfield in ts_type.fields:
      assert not isinstance(tsfield.decl.decl, str)
      field_assignments.append(
        ObjectInitField(
          tsfield.name,
          self._gen_uninit_field_assignment(tsfield.decl.decl, f'{wire_arg}.{tsfield.name}', self_type=py_type),
        )
      )

    object_init = ObjectInit(field_assignments)
    wire_func_name = f'convert{ts_type.name}ToWire'
    wire_func = gen_wire_func(wire_func_name, ts_type.name, object_init)

    self.serialize_wire_func_name[py_type] = wire_func_name
    self.serialize_wire_func[py_type] = wire_func

    return wire_func
