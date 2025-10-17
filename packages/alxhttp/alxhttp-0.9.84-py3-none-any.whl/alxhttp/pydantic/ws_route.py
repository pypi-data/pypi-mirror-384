from collections.abc import Awaitable
from dataclasses import dataclass
from functools import partial
from typing import Any, Callable, TypeAliasType, TypeVar, cast

import humps
from aiohttp import web
from aiohttp.web_request import Request as WebRequest
from aiohttp.web_response import StreamResponse
from aiohttp.web_urldispatcher import UrlDispatcher
from pydantic import BaseModel

from alxhttp.pydantic.basemodel import Empty, ErrorModel
from alxhttp.pydantic.route import BaseRouteDetails
from alxhttp.pydantic.ws_request import WSRequest
from alxhttp.server import Server

# from alxhttp.server import Server, ServerType

ErrorType = TypeVar('ErrorType', bound=ErrorModel)

MatchInfoType = TypeVar('MatchInfoType', bound=BaseModel)
BodyType = TypeVar('BodyType', bound=BaseModel)
QueryType = TypeVar('QueryType', bound=BaseModel)
ClientMsgType = TypeVar('ClientMsgType')
ServerMsgType = TypeVar('ServerMsgType')


@dataclass
class WSRouteDetails[ErrorType](BaseRouteDetails[ErrorType]):
  client_msg: type
  server_msg: type


def get_ws_route_details(func: Callable[..., Any]) -> WSRouteDetails[Any]:
  return WSRouteDetails(
    name=func._alxhttp_route_name,  # pyright: ignore[reportFunctionMemberAccess]
    match_info=func._alxhttp_match_info,  # pyright: ignore[reportFunctionMemberAccess]
    query=func._alxhttp_query,  # pyright: ignore[reportFunctionMemberAccess]
    client_msg=func._alxhttp_client_msg,  # pyright: ignore[reportFunctionMemberAccess]
    server_msg=func._alxhttp_server_msg,  # pyright: ignore[reportFunctionMemberAccess]
    ts_name=func._alxhttp_ts_name,  # pyright: ignore[reportFunctionMemberAccess]
    errors=func._alxhttp_errors or [],  # pyright: ignore[reportFunctionMemberAccess]
  )


class EmptyMsg(BaseModel):
  pass


# F = TypeVar('F', bound=Callable[..., Any])
ServerType = TypeVar('ServerType', bound=Server)
type TypedRequestHandler[ServerType, ServerMsgType, MatchInfoType, QueryType, T] = Callable[[ServerType, WSRequest[ServerMsgType, MatchInfoType, QueryType]], Awaitable[web.WebSocketResponse]]
type RequestHandler[ServerType] = Callable[[ServerType, WebRequest], Awaitable[StreamResponse]]


def ws_route(
  name: str,
  client_msg: type[ClientMsgType] | TypeAliasType,
  server_msg: type[ServerMsgType] | TypeAliasType,
  ts_name: str | None = None,
  match_info: type[MatchInfoType] = Empty,
  query: type[QueryType] = Empty,
  errors: list[type[ErrorType]] | None = None,
) -> Callable[[TypedRequestHandler[ServerType, ServerMsgType, MatchInfoType, QueryType, web.WebSocketResponse]], RequestHandler[ServerType]]:
  def decorator(
    func: TypedRequestHandler[ServerType, ServerMsgType, MatchInfoType, QueryType, web.WebSocketResponse],
  ) -> RequestHandler[ServerType]:
    new_ts_name = ts_name
    if not new_ts_name:
      new_ts_name = humps.camelize(func.__name__)

    async def wrapper(server: ServerType, request: web.Request, *args: Any, **kwargs: Any) -> web.WebSocketResponse:
      vr = await WSRequest[server_msg, match_info, query].from_request(request)
      return await func(server, vr, *args, **kwargs)

    assert name == name.strip()

    setattr(wrapper, '_alxhttp_route_name', name)
    setattr(wrapper, '_alxhttp_match_info', match_info)
    setattr(wrapper, '_alxhttp_query', query)
    setattr(wrapper, '_alxhttp_client_msg', client_msg)
    setattr(wrapper, '_alxhttp_server_msg', server_msg)
    setattr(wrapper, '_alxhttp_ts_name', new_ts_name)
    setattr(wrapper, '_alxhttp_errors', errors)
    return cast(RequestHandler[ServerType], wrapper)

  return decorator


def add_ws_route(
  server: ServerType,
  router: UrlDispatcher,
  route_handler: Callable[[ServerType, WebRequest], Awaitable[StreamResponse]],
) -> None:
  route_details = get_ws_route_details(route_handler)
  handler = partial(route_handler, server)
  router.add_route('GET', route_details.name, handler)
  print(f'- GET[ws] {route_details.name}')
  print(f'- GET[ws] {route_details.name}')
