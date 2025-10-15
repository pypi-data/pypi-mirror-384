from typing import override

import aiohttp
import aiohttp.abc
from multidict import CIMultiDict


class MultipartBytesWriter(aiohttp.abc.AbstractStreamWriter):
  data: bytes = b''

  @override
  async def write(self, chunk: bytes | bytearray | memoryview) -> None:
    self.data += chunk

  @override
  async def write_eof(self, chunk: bytes = b'') -> None:
    raise NotImplementedError()  # pragma: nocover

  @override
  async def drain(self) -> None:
    raise NotImplementedError()  # pragma: nocover

  @override
  def enable_compression(self, encoding: str = 'deflate', strategy: int | None = None) -> None:
    raise NotImplementedError()  # pragma: nocover

  @override
  def enable_chunking(self) -> None:
    raise NotImplementedError()  # pragma: nocover

  @override
  async def write_headers(self, status_line: str, headers: 'CIMultiDict[str]') -> None:
    raise NotImplementedError()  # pragma: nocover

  async def get_ct_and_bytes(self, mpw: aiohttp.MultipartWriter) -> tuple[str, bytes]:
    await mpw.write(self)
    return (f'multipart/text; boundary={mpw.boundary}', self.data)
