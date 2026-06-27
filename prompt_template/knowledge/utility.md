## CSA Checker Utility Functions

| Function | Description |
|----------|-------------|
| `ExprHasName(Expr, name)` | Check if expression matches function name |
| `getMemRegionFromExpr(C, Expr)` | Get memory region from expression |
| `markRegionChecked(State, MR)` | Mark region as null-checked |
| `reportUncheckedDereference(MR, C)` | Report null dereference bug |

## Program State Macros

- `PossibleNullPtrMap`: Tracks whether allocated regions have been null-checked
- `PtrAliasMap`: Tracks pointer aliasing between regions
