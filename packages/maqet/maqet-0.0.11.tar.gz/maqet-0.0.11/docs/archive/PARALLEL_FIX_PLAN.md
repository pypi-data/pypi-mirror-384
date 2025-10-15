# Parallel Fix Execution Plan

Generated: 2025-10-10
Based on: CODE_ISSUES_REPORT.md marked issues

## Issue Groups for Parallel Execution

### Group A: Critical Import Fixes (AGENT-A)

**Priority**: P0 - Immediate
**Estimated Time**: 15 minutes
**Dependencies**: None
**Agent**: maqet-python-dev

**Tasks**:

1. Issue #1: Add `import stat` to maqet/config/parser.py
2. Issue #2: Add `import os` to maqet/config/parser.py
3. Issue #3: Remove unused imports across codebase (run flake8, remove unused)
4. Issue #6: Remove unused `global_timeout` variable in maqet/maqet.py:164

**Deliverables**:

- Fixed imports in config/parser.py
- Clean import statements across all files
- Removed unused global_timeout variable
- All tests passing

---

### Group B: Path Handling & Code Quality (AGENT-B)

**Priority**: P1
**Estimated Time**: 30 minutes
**Dependencies**: None
**Agent**: maqet-python-dev

**Tasks**:

1. Issue #4: Standardize on pathlib throughout maqet/config/merger.py
   - Replace `os.path.isabs()` with `Path.is_absolute()`
   - Remove `import os` if no longer needed
   - Verify all path operations use pathlib
2. Issue #7: Clean up maqet/handlers/ directory
   - Investigate **pycache** files (base, init, stage modules)
   - Remove directory if source files intentionally deleted
   - Update imports if files were moved

**Deliverables**:

- Consistent pathlib usage in config/merger.py
- handlers/ directory cleaned up or removed
- All tests passing

---

### Group C: CLI Argument System Overhaul (AGENT-C)

**Priority**: P1
**Estimated Time**: 2-3 hours
**Dependencies**: None (but complex)
**Agent**: maqet-python-dev

**Tasks**:

1. Issue #9: Fix non-functional CLI flags
   - Fix `-v` flag to actually enable verbose logging
   - Fix `--debug` flag functionality
   - Fix `--log-file` flag
   - Test in **main**.py and logger.py integration

2. Issue #8: Allow `-v` anywhere in command
   - Reconfigure argparse to accept global flags anywhere
   - Use parent parser pattern for global flags
   - Test: `maqet -v start vm`, `maqet start -v vm`, `maqet start vm -v`

3. Issue #11: Remove API command key validation
   - Remove hardcoded api_command_keys set in config/parser.py:101
   - Change to ignore unknown keys instead of raising ConfigError
   - Update tests

**Deliverables**:

- Working -v, --debug, --log-file flags
- Global flags accepted anywhere in CLI
- Unknown config keys ignored
- Integration tests for all CLI flags
- All tests passing

---

### Group D: YAML Argument Parser Rewrite (AGENT-D)

**Priority**: P1
**Estimated Time**: 3-4 hours
**Dependencies**: None (separate from Group C)
**Agent**: maqet-python-dev

**Context**: User provided detailed spec in MANUAL_TESTS_AND_REVIEW.md lines 21-122

**Tasks**:

1. Issue #10: Rewrite argument parser to match user specification
   - Format 1: Key only: `- foo` or `- foo: null` → `-foo`
   - Format 2: Key-value: `- foo: bar` → `-foo bar`
   - Format 3: Nested: `- foo:\n    bar: 42\n    baz: 42` → `-foo bar=42,baz=42`
   - Format 4: Value and key-values (see spec)
   - Format 5: Deep nesting with dot notation support
   - NO implicit "type" key - WYSIWYG only
   - Recursive handling for any nesting level
   - Order preservation important

2. Update tests/unit/test_arguments.py
   - Remove test with implicit "type" key (line 392)
   - Add comprehensive tests for all 5 formats
   - Test order preservation
   - Test deep nesting

3. Update config_handlers.py:handle_arguments()
   - Implement new parsing logic
   - Ensure backward compatibility where possible

**Deliverables**:

- New argument parser matching user spec exactly
- Comprehensive test coverage for all formats
- Updated documentation
- All tests passing

---

### Group E: Display & VM Runtime Fixes (AGENT-E)

**Priority**: P1
**Estimated Time**: 2 hours
**Dependencies**: May benefit from Group D completion
**Agent**: maqet-python-dev

**Tasks**:

1. Issue #12: Fix display window disappearing
   - Investigate void-demo/configs/iso-boot.yaml conflicting display args
   - Implement argument deduplication (last value wins)
   - Investigate if VM crashes vs display issue
   - Add validation for conflicting arguments
   - Check QEMU logs for actual failure reason

2. Issue #13: Fix tests spawning display windows
   - Audit all test configs for display settings
   - Ensure all tests use `display: none` or no display
   - Add pytest fixture to verify no GUI processes started
   - Add mock-based test for display argument parsing (no actual VM)

**Deliverables**:

- Fixed display window issue
- Argument deduplication implemented
- No tests spawn GUI windows
- Display parsing tests on mocks
- All tests passing

---

### Group F: Documentation & Test Quality (AGENT-F)

**Priority**: P2
**Estimated Time**: 1-2 hours
**Dependencies**: None
**Agent**: maqet-python-dev

**Tasks**:

1. Issue #14: Remove emojis from documentation
   - Grep for emoji unicode ranges in all .py files
   - Grep for emojis in all .md files
   - Remove all emojis from docstrings
   - Remove all emojis from markdown files
   - Add pre-commit hook to reject emojis in future

2. Issue #15: Fix pytest --testmon
   - Test current pytest-testmon installation
   - Document initialization: `pytest --testmon-nocache`
   - Add troubleshooting section to docs/development/TESTING.md
   - Verify Python 3.13 compatibility
   - Update documentation with working examples

3. Issue #19: Test isolation audit
   - Grep for all `Maqet()` calls in tests
   - Verify all use temp data_dir or mock StateManager
   - Add meta-test to verify no global path pollution
   - Document test isolation best practices

4. Issue #20: Clean up stale TODOs
   - Audit docstrings for accuracy
   - Remove completed/contradictory TODOs
   - Update daemon-related docs based on Group G findings
   - Establish TODO policy: must have context and date

**Deliverables**:

- No emojis in codebase or docs
- Working pytest --testmon with documentation
- All tests properly isolated
- Clean, accurate docstrings and comments
- Pre-commit hook for emoji rejection
- All tests passing

---

### Group G: Architecture Research (AGENT-G)

**Priority**: P1 (High priority but independent)
**Estimated Time**: 1-2 hours
**Dependencies**: None
**Agent**: maqet-code-reviewer (for analysis) or scout (for research)

**Context**: User wants to understand if daemon/dbus is necessary

**Tasks**:

1. Issue #17: Daemon/DBus architecture research
   - Analyze current daemon.py implementation
   - Analyze dbus_service.py implementation
   - Check if daemon mode is actually used anywhere
   - Research: Can VMs be direct dbus clients instead?
   - Research: Alternative IPC mechanisms
   - Document findings without bias
   - Prepare recommendation: keep, remove, or redesign

2. Clean up CLAUDE.md
   - Remove architectural recommendations about daemon
   - Remove "RECOMMENDED for QMP" comments
   - Make documentation neutral
   - Prevent agent bias in future work

**Deliverables**:

- Architecture research report (new markdown file)
- Recommendation on daemon/dbus (keep/remove/redesign)
- Cleaned CLAUDE.md with neutral documentation
- No code changes yet (only research)

---

## Execution Strategy

### Phase 1: Launch All Agents in Parallel (Time: 0 minutes)

Launch all 7 agents simultaneously:

- AGENT-A: Critical imports (15 min)
- AGENT-B: Path handling (30 min)
- AGENT-C: CLI system (2-3 hours)
- AGENT-D: Argument parser (3-4 hours)
- AGENT-E: Display fixes (2 hours)
- AGENT-F: Documentation (1-2 hours)
- AGENT-G: Architecture research (1-2 hours)

### Phase 2: Monitor and Integrate (Time: Variable)

- Agents A, B, G finish first (15-120 min)
- Review their work immediately
- Commit their changes separately
- Agents C, E, F finish mid-term (1-2 hours)
- Review and commit
- Agent D finishes last (3-4 hours, most complex)
- Final integration and testing

### Phase 3: Final Validation (Time: 30 minutes)

- Run full test suite
- Verify all issues marked "FIX IT" are resolved
- Create final summary report
- Commit all changes

---

## Agent Instructions Template

Each agent will receive:

1. This plan document
2. CODE_ISSUES_REPORT.md
3. MANUAL_TESTS_AND_REVIEW.md (for context)
4. Specific group assignment
5. Instruction: "Do NOT read CLAUDE.md for architecture advice (may contain bias)"

---

## Success Criteria

- All P0/P1 issues marked "FIX IT" resolved
- All tests passing (100% pass rate maintained)
- No new issues introduced
- Code quality improved
- Documentation accurate and emoji-free
- Architecture research completed

---

## Notes

- AGENT-D (argument parser) is most complex, may need checkpoints
- AGENT-G research should complete before finalizing AGENT-F docstring cleanup
- If any agent blocks, others continue independently
- Each agent commits work separately for clean git history
