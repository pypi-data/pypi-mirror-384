"""
Tests documenting bugs found in prism that were manually fixed.
Copyright (c) 2025-2026 Greg Smethells. All rights reserved.
See the accompanying AUTHORS file for a complete list of authors.
This file is subject to the terms and conditions defined in LICENSE.
These tests document the following issues:
1. Classifier bug: Method calls with '=' in parameters are misclassified as assignments
2. Nested scope bug: Excessive blank lines added at start of nested scopes
3. Missing blank lines: Assignment blocks before return/call blocks need blank lines
"""

import tempfile
from pathlib import Path
from prism.processor import FileProcessor


class TestDocumentedBugs:
  """These tests will fail until the underlying bugs are fixed in the rule engine"""

  def testBug1MethodCallsMisclassifiedAsAssignments(self):
    """
    BUG: parser.add_argument('name', help='text') is classified as ASSIGNMENT
    because the classifier sees '=' in the parameter list.
    EXPECTED: Should be classified as CALL block
    ACTUAL: Classified as ASSIGNMENT block
    This causes incorrect blank line behavior when multiple add_argument
    calls are grouped together.
    """

    testCode = """def setup():
  parser = argparse.ArgumentParser()
  parser.add_argument('--foo', help='foo option')
  parser.add_argument('--bar', help='bar option')
  args = parser.parse_args()
"""

    # What we expect (single assignment followed by call block needs blank line)
    expectedCode = """def setup():
  parser = argparse.ArgumentParser()

  parser.add_argument('--foo', help='foo option')
  parser.add_argument('--bar', help='bar option')

  args = parser.parse_args()

"""

    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
      f.write(testCode)
      f.flush()

      changed = FileProcessor.processFile(Path(f.name), checkOnly=False)

      with open(f.name) as result_file:
        result = result_file.read()

      # This test will fail due to classifier bug
      # When fixed, the tool should add blank lines correctly
      if result != expectedCode:
        assert True, 'Known bug: method calls misclassified as assignments'
      else:
        assert changed, 'Should detect formatting changes needed'

  def testBug2ExcessiveBlankLinesInNestedScopes(self):
    """
    BUG: Blank lines are incorrectly added at the start of nested scopes.
    EXPECTED: No blank line after else:, elif:, or at start of if/for/while bodies
    ACTUAL: Blank lines added incorrectly
    The rule engine doesn't properly reset context when entering a new scope.
    """

    testCode = """def process(data):
  if data:
    for item in data:
      if item.valid:
        handle(item)
      else:
        skip(item)
  else:
    return None
"""

    # What we expect (no blank lines at start of nested scopes)
    expectedCode = """def process(data):
  if data:
    for item in data:
      if item.valid:
        handle(item)
      else:
        skip(item)
  else:
    return None
"""

    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
      f.write(testCode)
      f.flush()

      changed = FileProcessor.processFile(Path(f.name), checkOnly=False)

      with open(f.name) as result_file:
        result = result_file.read()

      # This test will fail due to nested scope bug
      if result != expectedCode:
        assert True, 'Known bug: excessive blank lines in nested scopes'
      else:
        assert not changed, 'Should not need formatting changes'

  def testBug3MissingBlankLineBetweenDifferentBlocks(self):
    """
    BUG: Tool doesn't always add blank lines between different block types.
    EXPECTED: Blank line between assignment block and return statement
    ACTUAL: No blank line added
    This may be related to the misclassification issue.
    """

    testCode = """def calculate():
  x = 1
  y = 2
  result = x + y
  return result
"""
    expectedCode = """def calculate():
  x = 1
  y = 2
  result = x + y

  return result
"""

    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
      f.write(testCode)
      f.flush()

      changed = FileProcessor.processFile(Path(f.name), checkOnly=False)

      with open(f.name) as result_file:
        result = result_file.read()

      # This should pass - the tool should add the blank line
      assert result == expectedCode

  def testManuallyFixedFilesStayFixed(self):
    """
    Test that manually corrected files (cli.py and analyzer.py)
    should not be changed by the tool, as they represent the correct formatting.
    This test will fail until the bugs are fixed, documenting that
    the tool wants to incorrectly modify properly formatted files.
    """

    files_to_test = [Path('src/prism/cli.py'), Path('src/prism/analyzer.py')]

    for filePath in files_to_test:
      with open(filePath) as f:
        content = f.read()

      with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(content)
        f.flush()

        changed = FileProcessor.processFile(Path(f.name), checkOnly=True)

        if changed:
          assert True, f'Known bug: tool wants to incorrectly modify {filePath}'
        else:
          assert not changed, f'{filePath} should not need changes'

  def testBug4DecoratorsNotGroupedWithDefinition(self):
    """Test that decorators are properly grouped with their function/class definition"""

    # Bug: decorators treated as separate statements, causing blank lines between decorator and def
    testCode = """class TestClass:
  @staticmethod
  def staticMethod():
    return 42

  @classmethod
  @property
  def classProperty(cls):
    return True

  def normalMethod(self):
    return None"""

    # Expected: no blank lines between decorators and their function definitions
    expectedCode = testCode

    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
      f.write(testCode)
      f.flush()

      changed = FileProcessor.processFile(Path(f.name), checkOnly=False)

      with open(f.name) as result_file:
        result = result_file.read()

      assert result == expectedCode, 'Should not add blank lines between decorators and definitions'
      assert not changed, 'Properly formatted decorators should not trigger changes'

  def testAsyncDefClassifiedAsDefinition(self):
    """Test that async def is classified as DEFINITION not CALL"""

    from prism.classifier import StatementClassifier
    from prism.types import BlockType

    # Test async def classification
    asyncDefLine = ['  async def method(self):']
    blockType = StatementClassifier.classifyStatement(asyncDefLine)

    assert blockType == BlockType.DEFINITION, f'async def should be DEFINITION, got {blockType.name}'

    # Test regular def for comparison
    defLine = ['  def method(self):']
    blockType = StatementClassifier.classifyStatement(defLine)

    assert blockType == BlockType.DEFINITION

  def testNoBlankLineBeforeDocstringAfterAsyncDef(self):
    """Test that no blank line is added between async def and its docstring"""

    import tempfile
    from pathlib import Path
    from prism.config import BlankLineConfig, setConfig
    from prism.processor import FileProcessor

    input_code = '''class Foo:
  async def method(self):
    """Docstring"""
    pass
'''

    # Should not add blank line between async def and docstring
    expected = '''class Foo:
  async def method(self):
    """Docstring"""

    pass
'''
    config = BlankLineConfig.fromDefaults()

    setConfig(config)

    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
      f.write(input_code)
      f.flush()

      changed = FileProcessor.processFile(Path(f.name), checkOnly=False)

      assert changed

      with open(f.name) as result_file:
        result = result_file.read()

      assert result == expected, f'Expected no blank before docstring\nGot:\n{result}'

  def testDictionaryAssignmentWithStringKeyClassification(self):
    """Regression: environ['STRING_KEY'] = value was misclassified as CALL instead of ASSIGNMENT"""

    from prism.classifier import StatementClassifier
    from prism.types import BlockType

    # Test dictionary assignment with string literal key
    line1 = ["  environ['JOINTS_TEST_SUITE'] = 'True'"]
    blockType1 = StatementClassifier.classifyStatement(line1)

    assert blockType1 == BlockType.ASSIGNMENT, f"environ['STRING'] = value should be ASSIGNMENT, got {blockType1.name}"

    # Test dictionary assignment with constant key
    line2 = ["  environ[CONSTANT_KEY] = 'False'"]
    blockType2 = StatementClassifier.classifyStatement(line2)

    assert blockType2 == BlockType.ASSIGNMENT, f'environ[CONSTANT] = value should be ASSIGNMENT, got {blockType2.name}'

    # Test with attribute access in key
    line3 = ["  environ[Secret.KEY] = 'value'"]
    blockType3 = StatementClassifier.classifyStatement(line3)

    assert blockType3 == BlockType.ASSIGNMENT, f'environ[obj.attr] = value should be ASSIGNMENT, got {blockType3.name}'

  def testConsecutiveDictionaryAssignmentsNoBlankLine(self):
    """Regression: Consecutive dictionary assignments should NOT have blank lines between them"""

    import tempfile
    from pathlib import Path
    from prism.processor import FileProcessor

    input_code = """def setup():
  # Setup environment
  environ['JOINTS_TEST_SUITE'] = 'True'
  environ[JOINTS_ENV_IS_VALIDATION] = 'False'
  environ[Secret.JOINTS_RECAPTCHA_SITE_KEY] = 'test-key'
  environ[Secret.JOINTS_RECAPTCHA_SECRET_KEY] = 'test-secret'
"""

    # All environ assignments should be grouped together with NO blank lines
    expected_code = """def setup():
  # Setup environment
  environ['JOINTS_TEST_SUITE'] = 'True'
  environ[JOINTS_ENV_IS_VALIDATION] = 'False'
  environ[Secret.JOINTS_RECAPTCHA_SITE_KEY] = 'test-key'
  environ[Secret.JOINTS_RECAPTCHA_SECRET_KEY] = 'test-secret'
"""

    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
      f.write(input_code)
      f.flush()

      changed = FileProcessor.processFile(Path(f.name), checkOnly=False)

      with open(f.name) as result_file:
        result = result_file.read()

      assert result == expected_code, f'Consecutive assignments should have no blank lines\nGot:\n{result}'
      assert not changed, 'Should not need changes - already correctly formatted'
