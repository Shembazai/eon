# EON PFA Demo Cases

These cases reflect validated deterministic flows and runtime behavior from the current personal-only branch.

## Case 1 - Deterministic monthly expense query

### Prompt
`what are my monthly expenses?`

### Expected behavior
The deterministic engine answers directly from the profile without using the model.

### Example output
`Estimated monthly expenses: $4210.00.`

## Case 2 - Income ratio query

### Prompt
`what percentage of my income goes to rent?`

### Expected behavior
The deterministic engine computes the category-to-income ratio directly from profile values.

### Example output
`17.25% of your income goes to rent. (Monthly income: $11596.00, rent: $2000.00)`

## Case 3 - Deterministic advice, mutation, and undo

### Prompt A
`give me actionable advice`

### Expected behavior
The decision layer produces deterministic advice grounded in the current profile.

### Example output
`Top finding: Rent at $2000.00 is materially larger than car loan at $600.00.
Action priorities:
1. The budget is concentrated in rent, so that line deserves review before scattered minor expenses.
Strength to preserve: The profile currently produces $7386.00 in monthly savings.`

### Prompt B
`replace rent with 1720`

### Expected behavior
The mutation firewall routes to deterministic profile modification, saves the change, and writes one journal row.

### Example output
`Saved changes: rent changed to $1720.00. Your estimated monthly income is now $11596.00, your total monthly expenses are $3930.00, and your monthly savings are $7666.00.`

### Prompt C
`undo last change`

### Expected behavior
The backup is restored and the undo does not create a new journal row.

### Example output
`Last saved change was undone. Your estimated monthly income is now $11596.00, your total monthly expenses are $4210.00, and your monthly savings are $7386.00.`

## Notes

- Core deterministic behavior remains available even when optional AI runtime is absent.
- Profile viewing remains available even when optional chart support is absent.
- Current branch is personal-only and deterministic-first by design.
