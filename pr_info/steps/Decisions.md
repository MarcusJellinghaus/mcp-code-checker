# Decisions

## Decision 1: Include `message` in known LogRecord fields

**Context:** Python's `LogRecord` has a `message` attribute (the formatted result of `msg % args`). Should we recognize it as a standard field?

**Decision:** Yes - add `message` to recognized fields for safety, handling edge cases where logging configuration or pytest plugins include it in output.

## Decision 2: Derive LOG_RECORD_FIELDS from dataclass

**Context:** Should we use an explicit constant listing all field names, or derive them automatically from the `LogRecord` dataclass?

**Decision:** Derive from dataclass with explanatory comment:
```python
# Derive known fields from LogRecord dataclass to auto-sync if fields are added.
# The "extra" field is excluded as it's our container for unknown fields.
LOG_RECORD_FIELDS = set(LogRecord.__dataclass_fields__.keys()) - {"extra"}
```

**Implication:** Since `message` needs to be a known field (Decision 1), it must be added as a field to the `LogRecord` dataclass itself.
