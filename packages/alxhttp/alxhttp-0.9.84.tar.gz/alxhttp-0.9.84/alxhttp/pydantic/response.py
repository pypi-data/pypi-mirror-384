from concurrent.futures import Executor
from typing import TypeVar

import pydantic
from aiohttp import web
from aiohttp.typedefs import LooseHeaders

from alxhttp.pydantic.basemodel import Empty

ResponseType = TypeVar('ResponseType', bound=pydantic.BaseModel)


class Response[ResponseType](web.Response):
  def __init__(
    self,
    *,
    body: ResponseType,
    status: int = 200,
    reason: str | None = None,
    headers: LooseHeaders | None = None,
    content_type: str | None = 'application/json',
    charset: str | None = None,
    zlib_executor_size: int | None = None,
    zlib_executor: Executor | None = None,
  ):
    super().__init__(
      body=None,
      status=status,
      reason=reason,
      text=body.model_dump_json(),  # pyright: ignore[reportAttributeAccessIssue, reportUnknownArgumentType]
      headers=headers,
      content_type=content_type,
      charset=charset,
      zlib_executor_size=zlib_executor_size,
      zlib_executor=zlib_executor,
    )


class EmptyResponse(Response[Empty]):
  def __init__(self):
    super().__init__(body=Empty())
