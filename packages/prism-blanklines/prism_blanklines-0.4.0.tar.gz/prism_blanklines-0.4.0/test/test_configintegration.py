"""
Integration tests for configuration system with file processing.
Copyright (c) 2025-2026 Greg Smethells. All rights reserved.
See the accompanying AUTHORS file for a complete list of authors.
This file is subject to the terms and conditions defined in LICENSE.
"""

import tempfile
from pathlib import Path
from prism.config import BlankLineConfig
from prism.processor import FileProcessor
from prism.types import BlockType


class TestConfigurationIntegration:
  def testDefaultConfigurationBehavior(self):
    """Test that default configuration produces expected 1-blank-line behavior"""

    input_code = """import sys
x = 1
def func():
  pass
if True:
  pass
"""
    expected_output = """import sys

x = 1

def func():
  pass

if True:
  pass

"""
    config = BlankLineConfig.fromDefaults()

    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
      f.write(input_code)
      f.flush()

      changed = FileProcessor.processFile(Path(f.name), config, checkOnly=False)

      assert changed

      with open(f.name) as result_file:
        result = result_file.read()

      assert result == expected_output

  def testZeroBlankLinesConfiguration(self):
    """Test custom configuration with 0 blank lines between different types"""

    input_code = """import sys

x = 1

def func():
  pass

if True:
  pass

"""

    # With 0 blank lines, should remove all blank lines between different types
    expected_output = """import sys
x = 1
def func():
  pass
if True:
  pass
"""
    config = BlankLineConfig(defaultBetweenDifferent=0)

    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
      f.write(input_code)
      f.flush()

      changed = FileProcessor.processFile(Path(f.name), config, checkOnly=False)

      assert changed

      with open(f.name) as result_file:
        result = result_file.read()

      assert result == expected_output

  def testTwoBlankLinesConfiguration(self):
    """Test custom configuration with 2 blank lines between different types"""

    input_code = """import sys
x = 1
def func():
  pass
"""
    expected_output = """import sys

x = 1

def func():
  pass

"""
    config = BlankLineConfig(defaultBetweenDifferent=2)

    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
      f.write(input_code)
      f.flush()

      changed = FileProcessor.processFile(Path(f.name), config, checkOnly=False)

      assert changed

      with open(f.name) as result_file:
        result = result_file.read()

      assert result == expected_output

  def testSpecificTransitionOverrides(self):
    """Test specific transition overrides work correctly"""

    input_code = """import sys
x = 1
print(x)
def func():
  pass
"""

    # Default 1, but assignment->call should be 0, import->assignment should be 2
    expected_output = """import sys

x = 1

print(x)

def func():
  pass

"""
    config = BlankLineConfig(
      defaultBetweenDifferent=1,
      transitions={
        (BlockType.ASSIGNMENT, BlockType.CALL): 0,  # x=1 -> print(x): no blank line
        (BlockType.IMPORT, BlockType.ASSIGNMENT): 2,  # import -> x=1: 2 blank lines
      },
    )

    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
      f.write(input_code)
      f.flush()

      changed = FileProcessor.processFile(Path(f.name), config, checkOnly=False)

      assert changed

      with open(f.name) as result_file:
        result = result_file.read()

      assert result == expected_output

  def testConsecutiveControlConfiguration(self):
    """Test consecutive control configuration works"""

    input_code = """if condition1:
  pass
if condition2:
  pass
"""

    # Default is 1, change to 2 blank lines between consecutive control
    expected_output = """if condition1:
  pass

if condition2:
  pass

"""
    config = BlankLineConfig(consecutiveControl=2)

    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
      f.write(input_code)
      f.flush()

      changed = FileProcessor.processFile(Path(f.name), config, checkOnly=False)

      assert changed

      with open(f.name) as result_file:
        result = result_file.read()

      assert result == expected_output

  def testConsecutiveDefinitionConfiguration(self):
    """Test consecutive definition configuration works"""

    input_code = """def func1():
  pass

def func2():
  pass

"""

    # Change to 0 blank lines between consecutive definitions
    expected_output = """def func1():
  pass
def func2():
  pass
"""
    config = BlankLineConfig(consecutiveDefinition=0)

    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
      f.write(input_code)
      f.flush()

      changed = FileProcessor.processFile(Path(f.name), config, checkOnly=False)

      assert changed

      with open(f.name) as result_file:
        result = result_file.read()

      assert result == expected_output

  def testComplexConfigurationScenario(self):
    """Test complex scenario with multiple configuration overrides"""

    input_code = """import sys
from os import path
x = 1
y = 2
print(x)
print(y)
def func1():
  pass
def func2():
  pass
if True:
  pass
if False:
  pass
"""
    config = BlankLineConfig(
      defaultBetweenDifferent=2,  # 2 blank lines by default
      consecutiveControl=0,  # No blank lines between consecutive control
      consecutiveDefinition=3,  # 3 blank lines between consecutive definitions
      transitions={
        (BlockType.IMPORT, BlockType.IMPORT): 0,  # No blank between imports
        (BlockType.ASSIGNMENT, BlockType.ASSIGNMENT): 1,  # 1 blank between assignments
        (BlockType.CALL, BlockType.CALL): 0,  # No blank between calls
        (BlockType.ASSIGNMENT, BlockType.CALL): 3,  # 3 blanks: assignment->call
      },
    )
    expected_output = """import sys
from os import path

x = 1
y = 2

print(x)
print(y)

def func1():
  pass

def func2():
  pass

if True:
  pass

if False:
  pass

"""

    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
      f.write(input_code)
      f.flush()

      changed = FileProcessor.processFile(Path(f.name), config, checkOnly=False)

      assert changed

      with open(f.name) as result_file:
        result = result_file.read()

      assert result == expected_output

  def testConfigurationDoesNotChangeAlreadyCorrectFile(self):
    """Test that correctly formatted files are not changed"""

    # This input is already correctly formatted for the custom config
    input_code = """import sys

x = 1

print(x)

def func():
  pass

"""
    config = BlankLineConfig(
      defaultBetweenDifferent=1,
      transitions={
        (BlockType.IMPORT, BlockType.ASSIGNMENT): 2,  # import->assignment: 2 blanks
        (BlockType.ASSIGNMENT, BlockType.CALL): 0,  # assignment->call: no blanks
      },
    )

    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
      f.write(input_code)
      f.flush()

      # Should return False (no changes needed)
      changed = FileProcessor.processFile(Path(f.name), config, checkOnly=False)

      assert not changed

      with open(f.name) as result_file:
        result = result_file.read()

      # Content should be unchanged
      assert result == input_code

  def testAfterDocstringConfiguration(self):
    """Test afterDocstring configuration controls blank lines after docstrings"""

    from prism.config import setConfig

    input_code = '''def func():
  """This is a docstring"""
  pass
'''

    # Test with default (1 blank line after docstring)
    expected_with_blank = '''def func():
  """This is a docstring"""

  pass
'''
    config_default = BlankLineConfig.fromDefaults()

    setConfig(config_default)

    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
      f.write(input_code)
      f.flush()

      changed = FileProcessor.processFile(Path(f.name), checkOnly=False)

      assert changed

      with open(f.name) as result_file:
        result = result_file.read()

      assert result == expected_with_blank

    # Test with afterDocstring=0 (no blank line after docstring)
    expected_no_blank = '''def func():
  """This is a docstring"""
  pass
'''
    config_compact = BlankLineConfig(afterDocstring=0)

    setConfig(config_compact)

    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
      f.write(input_code)
      f.flush()

      changed = FileProcessor.processFile(Path(f.name), checkOnly=False)

      assert not changed  # No changes needed since input already matches config

      with open(f.name) as result_file:
        result = result_file.read()

      assert result == expected_no_blank
