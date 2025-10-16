# Integration Tests for AII-Beta Session Output System

This directory contains integration tests for the complete session output system implementation.

## Test Structure

### Milestone Tests
- **`test_milestone1_simple_session.py`** - Basic session models functionality
- **`test_milestone2_session_manager.py`** - SessionManager with thread-safe operations
- **`test_milestone3_header_manager.py`** - OutputHeaderManager integration with sessions
- **`test_milestone3_header_visual.py`** - Visual tests for header formatting
- **`test_milestone4_footer_formatter.py`** - SessionFooterFormatter across verbosity levels
- **`test_complete_header_footer_system.py`** - Complete header-body-footer integration

## Running Integration Tests

### Run All Integration Tests
```bash
uv run pytest tests/integration/ -v
```

### Run Specific Milestone Tests
```bash
# Test session manager integration
uv run python tests/integration/test_milestone2_session_manager.py

# Test header manager integration
uv run python tests/integration/test_milestone3_header_manager.py

# Test footer formatter
uv run python tests/integration/test_milestone4_footer_formatter.py

# Test complete system
uv run python tests/integration/test_complete_header_footer_system.py
```

### Run Visual Tests
```bash
# Header visual formatting tests
uv run python tests/integration/test_milestone3_header_visual.py

# Footer visual formatting tests
uv run python tests/integration/test_milestone4_footer_formatter.py
```

## What These Tests Verify

### Session Foundation (M1-M2)
- SessionMetrics model functionality
- FunctionExecution tracking
- Thread-safe SessionManager operations
- Session lifecycle (start → track → finalize)

### Output System (M3-M4)
- OutputHeaderManager with session integration
- Three verbosity levels (minimal, standard, detailed)
- Function safety indicators and visual hierarchy
- SessionFooterFormatter with structured metrics
- Token tracking and cost estimation

### Complete Integration
- Header-body-footer architecture working together
- Multi-function pipeline visualization
- Error handling and edge cases
- Terminal compatibility (colors/emojis)

## Test Categories

### Unit Tests
Located in `tests/core/` and `tests/cli/` - Test individual components in isolation.

### Integration Tests
Located in `tests/integration/` - Test components working together and end-to-end scenarios.

### Manual Testing
Use the integration test scripts to manually verify visual output and behavior across different scenarios.

## Key Integration Scenarios

1. **Simple CLI Session** - Basic header → body → footer flow
2. **Multi-Function Pipeline** - Complex orchestrated function execution
3. **Error Scenarios** - Partial failures and error handling
4. **Verbosity Levels** - Different information levels for different users
5. **Terminal Compatibility** - Graceful fallbacks for different environments