from __future__ import annotations

import flatbuffers
import numpy as np

import flatbuffers
import typing

uoffset: typing.TypeAlias = flatbuffers.number_types.UOffsetTFlags.py_type

class ScalarType(object):
  FLOAT32: int
  FLOAT64: int
  FLOAT16: int
  BFLOAT16: int
  BOOL: int
  INT8: int
  INT16: int
  INT32: int
  INT64: int
  UINT8: int
  UINT16: int
  UINT32: int
  UINT64: int
  FLOAT8_E4M3FN: int
  FLOAT8_E4M3FNUZ: int
  FLOAT8_E5M2: int
  FLOAT8_E5M2FNUZ: int

