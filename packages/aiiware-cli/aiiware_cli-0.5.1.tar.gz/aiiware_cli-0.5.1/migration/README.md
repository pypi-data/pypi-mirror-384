# Migration Tools

This directory contains tools for migrating from AII v1 to v2 and ensuring parity.

## Tools

### Planned Files:

- `compare.py` - Compare v1 vs v2 command outputs
- `test_parity.py` - Automated parity testing
- `legacy_adapter.py` - Adapter for running v1 handlers in v2 architecture
- `migrate_patterns.py` - Extract patterns from v1 code to v2 YAML

## Usage

These tools will be used during development to ensure that v2 maintains compatibility with v1 functionality while adding new capabilities.

## Reference Implementation

v1 implementation is preserved in `aii_0_3_x/` for reference and comparison testing.