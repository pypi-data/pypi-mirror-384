from __future__ import annotations

import flatbuffers
import numpy as np

import flatbuffers
import typing

uoffset: typing.TypeAlias = flatbuffers.number_types.UOffsetTFlags.py_type

class Operator(object):
  _SOFTMAX: int
  _TO_COPY: int
  _UNSAFE_VIEW: int
  ADD_TENSOR: int
  ADDMM: int
  ALIAS: int
  ALL_DIM: int
  ARANGE: int
  ARANGE_START: int
  BITWISE_NOT: int
  BMM: int
  CAT: int
  CLONE: int
  COPY: int
  COS: int
  CUMSUM: int
  EMBEDDING: int
  EQ_SCALAR: int
  EXPAND: int
  FULL: int
  GELU: int
  GT_TENSOR: int
  LT_TENSOR: int
  MASKED_FILL_SCALAR: int
  MEAN_DIM: int
  MM: int
  MUL_SCALAR: int
  MUL_TENSOR: int
  NATIVE_LAYER_NORM: int
  NEG: int
  ONES: int
  ONES_LIKE: int
  PERMUTE: int
  POW_TENSOR_SCALAR: int
  RELU: int
  RSQRT: int
  RSUB_SCALAR: int
  SCALAR_TENSOR: int
  SILU: int
  SIN: int
  SLICE_TENSOR: int
  SLICE_SCATTER: int
  SPLIT_TENSOR: int
  SUB_TENSOR: int
  T: int
  TANH: int
  TRANSPOSE_INT: int
  TRIL: int
  TRIU: int
  UNSQUEEZE: int
  VIEW: int
  WHERE_SELF: int

