"""
Tests for statement classifier.
Copyright (c) 2025-2026 Greg Smethells. All rights reserved.
See the accompanying AUTHORS file for a complete list of authors.
This file is subject to the terms and conditions defined in LICENSE.
"""

from prism.classifier import StatementClassifier
from prism.types import BlockType


class TestStatementClassifier:
  def testAssignmentClassification(self):
    # Variable assignment
    assert StatementClassifier.classifyStatement(['x = 1']) == BlockType.ASSIGNMENT
    assert StatementClassifier.classifyStatement(['result = func()']) == BlockType.ASSIGNMENT

    # Multiline assignment
    lines = ['result = complexFunction(', '  arg1,', '  arg2', ')']

    assert StatementClassifier.classifyStatement(lines) == BlockType.ASSIGNMENT

  def testCallClassification(self):
    assert StatementClassifier.classifyStatement(['func()']) == BlockType.CALL
    assert StatementClassifier.classifyStatement(['return x']) == BlockType.CALL
    assert StatementClassifier.classifyStatement(['pass']) == BlockType.CALL

  def testImportClassification(self):
    assert StatementClassifier.classifyStatement(['import sys']) == BlockType.IMPORT
    assert StatementClassifier.classifyStatement(['from os import path']) == BlockType.IMPORT

  def testControlClassification(self):
    assert StatementClassifier.classifyStatement(['if True:']) == BlockType.CONTROL
    assert StatementClassifier.classifyStatement(['for i in range(10):']) == BlockType.CONTROL
    assert StatementClassifier.classifyStatement(['try:']) == BlockType.CONTROL

  def testDefinitionClassification(self):
    assert StatementClassifier.classifyStatement(['def func():']) == BlockType.DEFINITION
    assert StatementClassifier.classifyStatement(['class MyClass:']) == BlockType.DEFINITION
    assert StatementClassifier.classifyStatement(['@decorator']) == BlockType.DEFINITION

  def testSecondaryClause(self):
    assert StatementClassifier.isSecondaryClause('elif condition:')
    assert StatementClassifier.isSecondaryClause('else:')
    assert StatementClassifier.isSecondaryClause('except Exception:')
    assert StatementClassifier.isSecondaryClause('finally:')
    assert not StatementClassifier.isSecondaryClause('if condition:')
