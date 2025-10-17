import functools
from collections.abc import Awaitable
from dataclasses import dataclass
from functools import partial
from typing import Any, Callable, TypeVar, cast

import humps
from aiohttp import web
from aiohttp.web_request import Request as WebRequest
from aiohttp.web_response import StreamResponse
from aiohttp.web_urldispatcher import UrlDispatcher

from alxhttp.pydantic.basemodel import Empty, ErrorModel
from alxhttp.pydantic.request import BodyType, MatchInfoType, QueryType, Request
from alxhttp.pydantic.response import Response, ResponseType
from alxhttp.server import Server

# from alxhttp.server import ServerType

ErrorType = TypeVar('ErrorType', bound=ErrorModel)


@dataclass
class BaseRouteDetails[ErrorType]:
  name: str
  match_info: type
  query: type
  ts_name: str
  errors: list[type[ErrorType]]


@dataclass
class RouteDetails[ErrorType](BaseRouteDetails[ErrorType]):
  verb: str
  body: type
  response: type


def get_route_details(func: Callable[..., Any]) -> RouteDetails[Any]:
  return RouteDetails(
    name=func._alxhttp_route_name,  # pyright: ignore[reportFunctionMemberAccess]
    verb=func._alxhttp_route_verb,  # pyright: ignore[reportFunctionMemberAccess]
    match_info=func._alxhttp_match_info,  # pyright: ignore[reportFunctionMemberAccess]
    response=func._alxhttp_response,  # pyright: ignore[reportFunctionMemberAccess]
    body=func._alxhttp_body,  # pyright: ignore[reportFunctionMemberAccess]
    query=func._alxhttp_query,  # pyright: ignore[reportFunctionMemberAccess]
    ts_name=func._alxhttp_ts_name,  # pyright: ignore[reportFunctionMemberAccess]
    errors=func._alxhttp_errors or [],  # pyright: ignore[reportFunctionMemberAccess]
  )


# F = TypeVar('F', bound=Callable[..., Any])

ServerType = TypeVar('ServerType', bound=Server)
type TypedRequestHandler[ServerType, MatchInfoType, BodyType, QueryType, T] = Callable[[ServerType, Request[MatchInfoType, BodyType, QueryType]], Awaitable[Response[T]]]
type RequestHandler[ServerType] = Callable[[ServerType, WebRequest], Awaitable[StreamResponse]]


def route(
  verb: str,
  name: str,
  ts_name: str | None = None,
  match_info: type[MatchInfoType] = Empty,
  body: type[BodyType] = Empty,
  query: type[QueryType] = Empty,
  response: type[ResponseType] = Empty,
  errors: list[type[ErrorType]] | None = None,
) -> Callable[[TypedRequestHandler[ServerType, MatchInfoType, BodyType, QueryType, ResponseType]], RequestHandler[ServerType]]:
  def decorator(
    func: TypedRequestHandler[ServerType, MatchInfoType, BodyType, QueryType, ResponseType],
  ) -> RequestHandler[ServerType]:
    new_ts_name = ts_name
    if not new_ts_name:
      new_ts_name = humps.camelize(func.__name__)

    @functools.wraps(func)
    async def wrapper(server: ServerType, request: web.Request, *args: Any, **kwargs: Any) -> Response[ResponseType]:
      vr = await Request[match_info, body, query].from_request(request)
      return await func(server, vr, *args, **kwargs)

    assert name == name.strip()

    setattr(wrapper, '_alxhttp_route_name', name)
    setattr(wrapper, '_alxhttp_route_verb', verb)
    setattr(wrapper, '_alxhttp_match_info', match_info)
    setattr(wrapper, '_alxhttp_response', response)
    setattr(wrapper, '_alxhttp_body', body)
    setattr(wrapper, '_alxhttp_query', query)
    setattr(wrapper, '_alxhttp_ts_name', new_ts_name)
    setattr(wrapper, '_alxhttp_errors', errors)
    return cast(RequestHandler[ServerType], wrapper)

  return decorator


def add_route(
  server: ServerType,
  router: UrlDispatcher,
  route_handler: Callable[[ServerType, WebRequest], Awaitable[StreamResponse]],
) -> None:
  route_details = get_route_details(route_handler)
  handler = partial(route_handler, server)
  router.add_route(route_details.verb, route_details.name, handler)
  print(f'- {route_details.verb} {route_details.name}')
  print(f'- {route_details.verb} {route_details.name}')
