from dataclasses import dataclass, field
from typing import override

from alxhttp.typescript.basic_syntax import braces, join, space
from alxhttp.typescript.type_checks import is_class_var_or_annotated_class_var
from alxhttp.typescript.type_conversion import pytype_to_tstype


@dataclass
class Arg:
  name: str
  type_decl: str | type
  default_value: str | None = field(default=None)

  @override
  def __str__(self) -> str:
    if isinstance(self.type_decl, str):
      type_decl = self.type_decl
    else:
      type_decl = pytype_to_tstype(self.type_decl)
    default_decl = ''
    if self.default_value:
      default_decl = f' = {self.default_value}'
    return f'{self.name}: {type_decl}{default_decl}'


@dataclass
class Statement:
  pass


@dataclass
class Destructure(Statement):
  name: str
  arguments: list[str]

  @override
  def __str__(self) -> str:
    return space(f'const {{ {join(self.arguments, sep=", ")} }} = {self.name};')


@dataclass
class ReturnFuncCall(Statement):
  name: str
  arguments: list[str]
  is_async: bool = field(default=True)

  @override
  def __str__(self) -> str:
    await_expr = 'await ' if self.is_async else ''
    return space(f'return {await_expr}{self.name}({{ {join(self.arguments, sep=", ")} }});')


@dataclass
class If(Statement):
  cond: str
  stmts: list[Statement]

  @override
  def __str__(self) -> str:
    return space(f'if ({self.cond}) {{ {join(self.stmts)} }}')


@dataclass
class SwitchStmt(Statement):
  cond: str
  case_stmts: list[tuple[str, Statement]]
  default_stmt: Statement

  @override
  def __str__(self) -> str:
    cases = join([f'case {cond}: {{ {stmt} }}' for cond, stmt in self.case_stmts] + [f'default: {{ {self.default_stmt} }}'])

    return space(f'switch ({self.cond}) {{ {cases} }}')


@dataclass
class TryCatch(Statement):
  try_stmts: list[Statement]
  catch_stmts: list[Statement]

  @override
  def __str__(self) -> str:
    return space(f'try {{ {join(self.try_stmts)} }} catch(error: any) {{ {join(self.catch_stmts)} }}')


@dataclass
class AnonFuncCall(Statement):
  statements: list[str]

  @override
  def __str__(self) -> str:
    return space(f'() => {{ }} {{ {join(self.statements, sep="\n")} }}')


@dataclass
class CheckedParamsAccess(Statement):
  name: str

  @override
  def __str__(self) -> str:
    return space(f"""const {self.name} = params.{self.name};
                 if (!{self.name}) {{ throw Error('failed to access param'); }}
""")


@dataclass
class CheckedFormAccess(Statement):
  name: str

  @override
  def __str__(self) -> str:
    return space(f"""const {self.name} = formData.get('{self.name}')?.toString();
                 if (!{self.name}) {{ throw Error('failed to access form data'); }}
""")


@dataclass
class Func:
  name: str
  return_decl: str
  arguments: list[Arg]
  statements: list[Statement]
  is_async: bool = field(default=True)
  is_export: bool = field(default=False)

  @override
  def __str__(self) -> str:
    export = 'export ' if self.is_export else ''
    prefix = 'async ' if self.is_async else ''
    return f"""{export} {prefix} function {self.name}({join(self.arguments, sep=', ')}): {self.return_decl}
    {braces(self.statements)}\n\n"""


@dataclass
class RawStmt(Statement):
  stmt: str

  @override
  def __str__(self) -> str:
    return self.stmt


@dataclass
class JsonPost(Statement):
  url: str
  args: str
  response_type: str

  @override
  def __str__(self) -> str:
    return f"""
    const response = await postJSON(`{self.url}`, {self.args});
    
    if (response.status == 200 && response.body) {{
        return [get{self.response_type}FromWire(response.body), response];
    }}
    // throw new Error(`POST failed: ${{response.status}} ${{response.text}}`);
    return [null, response];
    
    """


@dataclass
class JsonGet(Statement):
  url: str
  response_type: str

  @override
  def __str__(self) -> str:
    return f"""
    const response = await getJSON(`{self.url}`);
    
    if (response.status == 200 && response.body) {{
        return [get{self.response_type}FromWire(response.body), response];
    }}
    // throw new Error(`GET failed: ${{response.status}} ${{response.text}}`);
    return [null, response];
    
    """


@dataclass
class TypeDecl:
  decl: type | str
  self_type: type | None = None

  def __init__(self, decl: type | str, self_type: type | None = None):
    if is_class_var_or_annotated_class_var(decl):
      print('ignoring class var', decl)
    self.decl = decl
    self.self_type = self_type
    if 'Self' in str(decl) and self_type is None:
      raise ValueError('Self type is required')

  @override
  def __str__(self) -> str:
    if isinstance(self.decl, str):
      raise ValueError
    return pytype_to_tstype(self.decl, self_type=self.self_type)


@dataclass
class ObjectTypeField:
  name: str
  decl: TypeDecl
  default_value: str | None

  @override
  def __str__(self) -> str:
    default_value = f' = {self.default_value}' if self.default_value else ''
    return f'{self.name}: {self.decl}{default_value}'


@dataclass
class ObjectType:
  name: str
  fields: list[ObjectTypeField]
  export: bool = True

  @override
  def __str__(self) -> str:
    export_decl = 'export ' if self.export else ''
    if not self.fields:
      return f'{export_decl}type {self.name} = Record<string, unknown>\n\n'
    return f'{export_decl}type {self.name} = {braces(self.fields, sep=",\n")}\n\n'


@dataclass
class UnionType:
  name: str
  members: list[str]
  export: bool = True

  @override
  def __str__(self) -> str:
    export_decl = 'export ' if self.export else ''
    assert self.members
    return f'{export_decl}type {self.name} = {"|".join(self.members)}\n\n'


@dataclass
class ObjectInitField:
  name: str
  value: str | None

  @override
  def __str__(self) -> str:
    return f'{self.name}: {self.value}'


@dataclass
class ObjectInit:
  fields: list[ObjectInitField]

  @override
  def __str__(self) -> str:
    return f'{braces(self.fields, sep=",\n")}\n'
