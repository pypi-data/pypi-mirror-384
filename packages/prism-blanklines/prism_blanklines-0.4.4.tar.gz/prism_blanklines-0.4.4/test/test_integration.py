"""
Integration tests with known input/output pairs.
Copyright (c) 2025-2026 Greg Smethells. All rights reserved.
See the accompanying AUTHORS file for a complete list of authors.
This file is subject to the terms and conditions defined in LICENSE.
"""

import tempfile
from pathlib import Path
from prism.processor import FileProcessor


class TestIntegration:
  def testBasicBlankLineRules(self):
    """Test basic blank line rules between different block types (PEP 8 compliant)"""

    input_code = """import sys
x = 1
def foo():
  pass
if True:
  pass
"""

    # PEP 8: 2 blank lines around module-level definitions
    expected_output = """import sys

x = 1


def foo():
  pass


if True:
  pass
"""

    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
      f.write(input_code)
      f.flush()

      # Process the file
      changed = FileProcessor.processFile(Path(f.name), checkOnly=False)

      assert changed

      # Read the result
      with open(f.name) as result_file:
        result = result_file.read()

      assert result == expected_output

      # Verify idempotency - second run should not change anything
      changed_again = FileProcessor.processFile(Path(f.name), checkOnly=True)

      assert not changed_again

  def testSecondaryClauseRules(self):
    """Test that secondary clauses don't get blank lines before them"""

    input_code = """if condition:
  pass
else:

  pass

try:
  pass
except Exception:
  pass
finally:
  pass

"""
    expected_output = """if condition:
  pass
else:
  pass

try:
  pass
except Exception:
  pass
finally:
  pass
"""

    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
      f.write(input_code)
      f.flush()

      changed = FileProcessor.processFile(Path(f.name), checkOnly=False)

      assert changed

      with open(f.name) as result_file:
        result = result_file.read()

      assert result == expected_output

  def testCommentBreakRules(self):
    """Test comment break behavior"""

    input_code = """x = 1

# Comment causes break
y = 2

# Another comment
z = 3

"""
    expected_output = """x = 1

# Comment causes break
y = 2

# Another comment
z = 3
"""

    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
      f.write(input_code)
      f.flush()

      changed = FileProcessor.processFile(Path(f.name), checkOnly=False)

      assert changed

      with open(f.name) as result_file:
        result = result_file.read()

      assert result == expected_output

  def testMultilineStatements(self):
    """Test multiline statement classification and blank line rules"""

    input_code = """result = complexFunction(
  arg1,
  arg2
)
x = 1
def func():
  pass
"""

    # Assignment block groups together, then PEP 8: 2 blank lines before module-level def
    expected_output = """result = complexFunction(
  arg1,
  arg2
)
x = 1


def func():
  pass
"""

    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
      f.write(input_code)
      f.flush()

      changed = FileProcessor.processFile(Path(f.name), checkOnly=False)

      assert changed

      with open(f.name) as result_file:
        result = result_file.read()

      assert result == expected_output

  def testPEP8ModuleLevelDefinitions(self):
    """Test PEP 8: 2 blank lines between top-level function/class definitions"""

    input_code = """def func1():
  pass
def func2():
  pass

class MyClass:
  pass
"""
    expected_output = """def func1():
  pass


def func2():
  pass


class MyClass:
  pass
"""

    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
      f.write(input_code)
      f.flush()

      changed = FileProcessor.processFile(Path(f.name), checkOnly=False)

      assert changed

      with open(f.name) as result_file:
        result = result_file.read()

      assert result == expected_output

  def testPEP8ClassMethodDefinitions(self):
    """Test PEP 8: 1 blank line between method definitions inside class"""

    input_code = """class MyClass:
  def method1(self):
    pass
  def method2(self):
    pass
"""
    expected_output = """class MyClass:
  def method1(self):
    pass

  def method2(self):
    pass
"""

    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
      f.write(input_code)
      f.flush()

      changed = FileProcessor.processFile(Path(f.name), checkOnly=False)

      assert changed

      with open(f.name) as result_file:
        result = result_file.read()

      assert result == expected_output
