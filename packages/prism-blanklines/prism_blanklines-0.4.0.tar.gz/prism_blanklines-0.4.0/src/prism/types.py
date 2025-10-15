"""
Core types and data structures for prism.
Copyright (c) 2025-2026 Greg Smethells. All rights reserved.
See the accompanying AUTHORS file for a complete list of authors.
This file is subject to the terms and conditions defined in LICENSE.
"""

from dataclasses import dataclass
from enum import Enum


class BlockType(Enum):
  """Block types in precedence order"""

  ASSIGNMENT = 1
  CALL = 2
  IMPORT = 3
  CONTROL = 4
  DEFINITION = 5
  DECLARATION = 6
  DOCSTRING = 7
  COMMENT = 8


@dataclass
class Statement:
  """Represents a logical statement that may span multiple lines"""

  lines: list[str]
  startLineIndex: int
  endLineIndex: int
  blockType: BlockType
  indentLevel: int
  isComment: bool = False
  isBlank: bool = False
  isSecondaryClause: bool = False
