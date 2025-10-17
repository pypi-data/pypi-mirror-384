#!/usr/bin/env python3
"""Debug import followed by call."""

from prism.analyzer import FileAnalyzer
from prism.rules import BlankLineRuleEngine
from prism.config import BlankLineConfig, setConfig

code = """  import asyncio
  from time import time
  from tornado.httpclient import HTTPRequest, HTTPResponse
  daemon.reset_mock()
  # Mock the HTTP client
  async def exactRPCResponse(*args, **kwargs):
    await asyncio.sleep(0)
"""

config = BlankLineConfig(afterDocstring=0)
setConfig(config)

lines = code.split('\n')
print(f'Input lines ({len(lines)} total):')
for i, line in enumerate(lines):
  marker = '[BLANK]' if not line.strip() else ''
  print(f'  {i}: "{line}" {marker}')

analyzer = FileAnalyzer()
statements = analyzer.analyzeFile(lines)

print(f'\nTotal statements: {len(statements)}')
print('\nStatement details:')
for i, stmt in enumerate(statements):
  if stmt.isBlank:
    print(f'{i}: BLANK')
  else:
    firstLine = stmt.lines[0][:70] if stmt.lines else ''
    print(f'{i}: {stmt.blockType.name:15} indent={stmt.indentLevel:2} lines={len(stmt.lines)} "{firstLine}"')

# Apply rules
engine = BlankLineRuleEngine()
blankLineCounts = engine.applyRules(statements)

print('\nBlank line counts:')
for i, count in enumerate(blankLineCounts):
  if not statements[i].isBlank:
    firstLine = statements[i].lines[0][:60] if statements[i].lines else ''
    marker = '***' if count > 0 else '   '
    print(f'{marker} {i}: {count} blank(s) before {statements[i].blockType.name:15} "{firstLine}"')
