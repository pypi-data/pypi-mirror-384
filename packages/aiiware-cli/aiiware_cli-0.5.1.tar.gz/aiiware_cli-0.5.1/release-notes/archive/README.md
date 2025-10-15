# Archived Release Notes

This directory contains obsolete or superseded release documentation that is preserved for historical reference.

## Archived Documents

### `v0.1.0-streaming-clarification-OBSOLETE.md`

**Original Purpose:** Document that we were accepting batch-mode streaming for v0.1.0 and planning to implement true token-by-token streaming in v0.2.0.

**Why Archived:** We actually implemented real token-by-token streaming in v0.1.0 (via CLI v0.5.1), so this document became obsolete. The "Known Limitations" and "Option 1: Accept & Document" approach was never needed.

**Superseded By:**
- `release-notes/v0.5.1.md` - Documents the actual streaming implementation
- `system-design-docs/aii-cli-0.5.1-streaming-implementation-summary.md` - Complete technical implementation
- `release-notes/v0.5.1-and-vscode-0.1.0-documentation-updates.md` - Documentation update summary

**Date Archived:** 2025-10-14

---

## Archive Policy

Documents are archived when:
1. They become obsolete due to implementation changes
2. They describe plans that were superseded by different approaches
3. They contain temporary decisions that were later reversed

Archived documents are kept for:
- Historical reference
- Understanding decision-making process
- Learning from planning vs. actual implementation
