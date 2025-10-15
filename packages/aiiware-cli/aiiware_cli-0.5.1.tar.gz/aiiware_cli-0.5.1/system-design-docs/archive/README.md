# Archived System Design Documents

This directory contains obsolete or superseded system design documentation that is preserved for historical reference.

## Archived Documents

### `aii-vscode-0.2.0-streaming-enhancement-OBSOLETE.md`

**Original Purpose:** Planning document for implementing true token-by-token streaming in VSCode extension v0.2.0 and CLI v0.5.2.

**Why Archived:** We accelerated the implementation and delivered streaming in CLI v0.5.1 instead of v0.5.2, enabling VSCode v0.1.0 to launch with real streaming rather than waiting for v0.2.0. The entire plan became obsolete when we decided to fix it immediately rather than defer it.

**Superseded By:**
- `system-design-docs/aii-cli-0.5.1-streaming-implementation-summary.md` - Actual implementation (v0.5.1, not v0.5.2)
- `release-notes/v0.5.1.md` - Complete release notes with streaming details
- VSCode v0.1.0 launched with streaming instead of v0.2.0

**Date Archived:** 2025-10-14

**Historical Value:** Shows the original plan and timeline we had before deciding to accelerate implementation. Useful for understanding how we prioritized user experience over planned release cycles.

---

## Archive Policy

Design documents are archived when:
1. They describe features that were implemented differently than planned
2. They target versions that were superseded (e.g., v0.5.2 → v0.5.1)
3. They become obsolete due to accelerated implementation timelines

Archived documents are kept for:
- Historical decision-making reference
- Understanding planning vs. actual implementation
- Learning from scope and timeline changes
- Documenting how priorities shifted based on user feedback
