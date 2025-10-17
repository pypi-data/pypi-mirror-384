import asyncio
import logging
from collections.abc import AsyncGenerator, Awaitable, Iterable
from typing import Callable, TypeVar

from aiohttp import web
from aiohttp.typedefs import Middleware
from aiohttp.web_request import Request
from aiohttp.web_response import StreamResponse

from alxhttp.logging import JSONAccessLogger, get_json_server_logger
from alxhttp.middleware.defaults import default_middleware


class Server:
  app: web.Application
  host: str
  port: int
  shutdown_event: asyncio.Event

  def __init__(
    self,
    middlewares: Iterable[Middleware] | None = None,
    logger: logging.Logger | None = None,
  ):
    if middlewares is None:
      middlewares = default_middleware()
    if logger is None:
      logger = get_json_server_logger()
    self.app = web.Application(middlewares=middlewares, logger=logger)
    self.host = ''
    self.port = 0
    self.shutdown_event = asyncio.Event()

  async def setup_ctx(self, app: web.Application) -> AsyncGenerator[None, None]:
    """
    Base classes should async-with all their stateful things and yield once.
    When the app shuts down it will return to this generator so they can unwind.
    """
    yield

  async def run_app(self, log: logging.Logger, host: str = 'localhost', port: int = 0) -> None:
    self.app.cleanup_ctx.append(self.setup_ctx)

    runner = web.AppRunner(self.app, debug=True, access_log_class=JSONAccessLogger)
    await runner.setup()
    site: web.TCPSite = web.TCPSite(runner, host, port)

    await site.start()

    self.host = host
    self.port = port
    assert isinstance(site._server, asyncio.Server)
    assert len(site._server.sockets) > 0
    s = site._server.sockets[0]
    assert s
    p = s.getsockname()
    assert p
    self.port = p[1]
    log.info({'message': f'listening on {self.host}:{self.port}'})

    try:
      await self.shutdown_event.wait()
    except (asyncio.exceptions.CancelledError, KeyboardInterrupt):
      pass
    finally:
      await runner.cleanup()


ServerType = TypeVar('ServerType', bound=Server)

ServerHandler = Callable[[ServerType, Request], Awaitable[StreamResponse]]
