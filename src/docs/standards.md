# EON Development Standards

## Philosophy

EON is built as a deterministic, security-first system.
Clarity and control take priority over convenience.

## Rules

- No hidden behavior
- All state changes must be explicit
- Prefer simple, understandable logic over abstraction
- Every modification must be traceable
- Code should be readable without external context

## Structure

- Core logic lives in `src/`
- Documentation lives in `docs/`
- No mixing responsibilities

## Security

- Never introduce uncontrolled mutation
- Always preserve ability to audit or revert changes
