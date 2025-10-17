from __future__ import annotations

import flatbuffers
import numpy as np

import flatbuffers
import typing

uoffset: typing.TypeAlias = flatbuffers.number_types.UOffsetTFlags.py_type

class Empty(object):
  @classmethod
  def GetRootAs(cls, buf: bytes, offset: int) -> Empty: ...
  @classmethod
  def GetRootAsEmpty(cls, buf: bytes, offset: int) -> Empty: ...
  def Init(self, buf: bytes, pos: int) -> None: ...
def EmptyStart(builder: flatbuffers.Builder) -> None: ...
def EmptyEnd(builder: flatbuffers.Builder) -> uoffset: ...

