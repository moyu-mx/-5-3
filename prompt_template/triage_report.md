# Instruction
Determine whether the static analyzer report is a real bug in the Linux kernel and matches the target bug pattern.

Classify as:
- TP (matches the target bug pattern and is a real bug)
- FP (does not match the target pattern or not a real bug)

# Patch
{{ input_patch }}

# Target Pattern
{{ input_pattern }}

# Report
{{ input_report }}
