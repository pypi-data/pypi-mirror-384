# Command Pattern Definitions

This directory contains YAML files that define all available commands in the AII CLI system.

## Structure

Each YAML file defines a command family with the following structure:

```yaml
family: family_name
aliases: [primary, alt1, alt2]
summary: One-line description
commands:
  - id: family.command.variant
    name: command_name
    intent: What this command does
    entry_tokens: [main, shortcut]
    scope: global|session|repo
    patterns:
      - id: pattern_id
        syntax: 'human-readable syntax'
        regex: '^actual regex pattern$'
        priority: 10
    parameters:
      - name: param_name
        type: string|int|float|bool|path|enum
        required: true|false
        description: Parameter description
    handler: package.module.HandlerClass
    examples:
      - 'example usage 1'
    help:
      usage: 'command [options] <args>'
      notes:
        - Important note
      related: [related.command.1]
```

## Command Families

Files to be created:
- `translate.yaml` - Translation and localization commands
- `git.yaml` - Git workflow automation
- `shell.yaml` - Shell command execution
- `code.yaml` - Code generation and analysis
- `write.yaml` - Content writing assistance
- `analyze.yaml` - Code analysis tools
- `polish.yaml` - Text polishing and improvement
- `chat.yaml` - Interactive conversation mode
- `shortcuts.yaml` - Quick access shortcuts

## Validation

All YAML files are validated against the Pydantic schema defined in `aii.commands.schema`.
Invalid patterns will be rejected at load time with detailed error messages.