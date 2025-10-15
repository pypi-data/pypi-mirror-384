# Release Strategy Documentation

**Purpose**: Operational guides and checklists for releasing AII products
**Audience**: Release managers, developers preparing releases
**Scope**: All AII products (CLI, VSCode Extension, future products)

---

## 📁 What Goes Here

This folder contains **release processes, checklists, and operational guides** for publishing AII products to various distribution channels.

### ✅ Include in this folder:
- Pre-publication checklists
- Release process documentation
- Publishing guidelines
- Version coordination strategies
- Distribution channel requirements
- Quality gates and validation steps

### ❌ Do NOT include here:
- Release notes (historical) → Use `/release-notes/`
- Architecture documentation → Use `/system-design-docs/`
- Development plans → Use `/system-dev-docs/`
- Source code → Use product directories (`/aii/`, `/aii-vscode/`)

---

## 📄 Current Documents

### VSCode Extension
- **[vscode-pre-publication-checklist.md](./vscode-pre-publication-checklist.md)** - Complete checklist for publishing VSCode extension to marketplace

### CLI (Future)
- `cli-pypi-publication-checklist.md` - *(To be created)* Guide for publishing CLI to PyPI
- `cli-versioning-strategy.md` - *(To be created)* CLI version management

### Cross-Product (Future)
- `version-coordination-guide.md` - *(To be created)* How CLI and VSCode versions relate
- `release-calendar-template.md` - *(To be created)* Coordinated release planning

---

## 🎯 Folder Philosophy

### Separation of Concerns

```
/release-notes/         # WHAT was released (historical records)
/release-strategy/      # HOW to release (operational processes)
/system-design-docs/    # WHY architecture decisions were made
/system-dev-docs/       # WHEN features will be developed (plans)
```

**Example Flow**:
1. Developer builds feature (follows `/system-dev-docs/`)
2. Release manager follows checklist (uses `/release-strategy/`)
3. Product is published (creates entry in `/release-notes/`)

### Version-Specific vs. Process Documentation

| Type | Location | Example |
|------|----------|---------|
| **Version-specific** | `/release-notes/` | `v0.1.0.md` - What changed in this version |
| **Process** | `/release-strategy/` | `vscode-pre-publication-checklist.md` - How to publish any version |

---

## 🚀 Using These Guides

### For VSCode Extension Release:
1. Open `vscode-pre-publication-checklist.md`
2. Follow all 6 phases sequentially
3. Check off items as completed
4. Only publish when all ✅

### For CLI Release (Future):
1. Open `cli-pypi-publication-checklist.md`
2. Follow checklist steps
3. Coordinate with VSCode release if needed (see version coordination guide)

---

## 📚 Related Documentation

- **Product Descriptions**: `/system-design-docs/product-description-updates-2025-10.md`
- **Keywords Strategy**: `/system-design-docs/keywords-strategy-hybrid-approach.md`
- **Release Notes**: `/release-notes/` (version-specific historical records)
- **VSCode Versioning**: `/aii-vscode/VERSIONING.md` (internal, not published)
- **VSCode Development**: `/aii-vscode/DEVELOPMENT.md` (internal, not published)

---

## 🔄 Maintenance

### When to Update Documents Here:
- Distribution platform changes requirements (e.g., VSCode Marketplace updates)
- New quality gates are added
- Process improvements are discovered
- New products are launched

### Who Maintains:
- Release managers own these documents
- Developers can suggest improvements via PR
- Review quarterly for accuracy

---

## 📋 Quick Reference

| Product | Checklist | Distribution | Current Version |
|---------|-----------|--------------|-----------------|
| **VSCode Extension** | [vscode-pre-publication-checklist.md](./vscode-pre-publication-checklist.md) | VSCode Marketplace | v0.1.0 |
| **CLI** | *(TBD)* | PyPI | v0.5.1 |

---

**Last Updated**: 2025-10-14
**Maintained By**: Release Engineering Team
