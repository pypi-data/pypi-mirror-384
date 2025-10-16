# Phase 2 Complete: Design Documentation

**Date**: 2025-10-12
**Status**: ✅ COMPLETE

## What We Accomplished

### 📄 Documentation Created

1. **`docs/DESIGN.md`** (600+ lines)
   - Complete architectural design
   - AST node definitions with type hints
   - State machine design for mrkdwn parser
   - Visitor pattern for renderers
   - Exception hierarchy
   - API design (simple + advanced)
   - Implementation order with time estimates
   - Migration guide from v0.1.0

2. **`docs/QUICK_REFERENCE.md`**
   - State machine quick reference
   - Visitor pattern examples
   - API examples
   - Critical implementation details
   - Implementation checklist

3. **`TDD_STATUS.md`** (updated)
   - Phase 1 & 2 completion status
   - Next steps for Phase 3

## Key Design Decisions

### 1. State Machine for Mrkdwn Parser

**Two states**:
- `OUTSIDE_CODE_BLOCK`: Parse formatting, links, mentions
- `IN_CODE_BLOCK`: Everything is literal text, strip angle brackets from URLs

**Why**: Context-dependent rules require different parsing logic inside/outside code blocks.

**Example**:
```
Input: "text *bold* ```<url>``` *bold*"

OUTSIDE: *bold* → parse as bold
IN_CODE: *bold* → literal text
IN_CODE: <url> → url (strip brackets)
OUTSIDE: *bold* → parse as bold
```

### 2. Visitor Pattern for Renderers

**Old approach**: Manual recursion
**New approach**: Renderers extend `NodeVisitor` base class

**Benefits**:
- Consistent tree traversal
- Easy to add new renderers (Jira, HTML, etc.)
- Testable (each visit method tested independently)
- Composable (combine multiple visitors)

**Example**:
```python
class GFMRenderer(NodeVisitor):
    def visit_Bold(self, node):
        self.output.append("**")
        for child in node.children:
            self.visit(child)
        self.output.append("**")
```

### 3. Exception Hierarchy

```
SlackGFMError
├── ParseError (invalid input)
├── RenderError (cannot produce output)
├── ValidationError (invalid data)
└── TransformError (visitor failed)
```

**Optional control**: `raise_on_error` parameter
- `True`: Raise exceptions for debugging
- `False`: Best-effort fallback (production)

### 4. New Features

#### Deep Linking
```python
gfm = rich_text_to_gfm(rich_text, team_id="T12345")
# Output: [@user](slack://user?team=T12345&id=U123)
```

#### AST Printer
```python
from slack_gfm.ast import print_ast
print(print_ast(ast))
# Document
#   Paragraph
#     Bold
#       Text: 'hello'
```

#### Advanced API
```python
ast = parse_rich_text(data)
ast = MyCustomVisitor().visit(ast)
gfm = render_gfm(ast)
```

## Implementation Order (Phase 3)

**Estimated time: ~25 hours**

1. Exception classes (1h)
2. AST refinements (2h)
3. Rich Text parser fixes (2h)
4. **Mrkdwn tokenizer with state machine (4h)** ← CRITICAL
5. Mrkdwn parser (3h)
6. GFM renderer - visitor-based (3h)
7. Rich Text renderer - visitor-based (2h)
8. AST printer (1h)
9. Deep linking (1h)
10. Error handling integration (2h)
11. Documentation (2h)
12. Final testing (2h)

## Success Criteria

- [ ] All 81 tests passing
- [ ] Coverage ≥ 85%
- [ ] No ruff/mypy errors
- [ ] Code blocks strip angle brackets from URLs (test-case-020)
- [ ] Round-trip conversions lossless
- [ ] Visitor pattern implemented consistently
- [ ] State machine handles edge cases

## Critical Fixes Addressed

### Issue 07: Angle Brackets in Code Blocks
**Problem**: `<https://example.com>` in code blocks keeps angle brackets
**Solution**: State machine strips brackets when `IN_CODE_BLOCK` state
**Proof**: test-case-020 screenshot shows URL without brackets

### Issue 08: Trailing Newlines
**Problem**: GFM → Rich Text adds extra newline to code blocks
**Solution**: Rich Text renderer strips trailing newline
```python
content = node.content.rstrip("\n")
```

### Combined Formatting
**Problem**: Bold+italic doesn't render correctly
**Solution**: Proper AST nesting in Rich Text parser
```python
node = Text(text=text)
if style.get("bold"):
    node = Bold(children=[node])
if style.get("italic"):
    node = Italic(children=[node])
```

## Files Structure

```
slack-gfm/
├── docs/
│   ├── DESIGN.md              ← Complete design spec
│   └── QUICK_REFERENCE.md     ← Implementation cheatsheet
├── tests/
│   ├── test_real_world_cases.py  ← 81 tests from real data
│   └── test_issue_fixes.py       ← Tests for specific bugs
├── .test-cases/               ← 27 real Slack messages
│   ├── test-case-001/
│   │   ├── screenshot.png
│   │   ├── rich_text.json
│   │   ├── mrkdwn.txt
│   │   └── description.txt
│   └── ...
├── TDD_STATUS.md              ← Overall progress
└── PHASE_2_SUMMARY.md         ← This file
```

## What's Next?

**Ready for Phase 3: Implementation!**

We now have:
✅ 81 comprehensive tests (baseline: 45 passing, 36 failing)
✅ Complete design documentation
✅ State machine architecture defined
✅ Visitor pattern specified
✅ Clear implementation order

**First step of Phase 3**: Implement exception classes (1 hour)

---

**Questions or concerns about the design?** This is the time to discuss before we start coding!
