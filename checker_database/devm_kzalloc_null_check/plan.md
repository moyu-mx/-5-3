## Detection Plan

1. Program State Management: Use PossibleNullPtrMap
2. checkPostCall: Track devm_kzalloc allocations
3. checkBranchCondition: Detect null checks including unlikely(!ptr)
4. checkBind: Track pointer aliasing
5. checkLocation: Warn on unchecked dereference
