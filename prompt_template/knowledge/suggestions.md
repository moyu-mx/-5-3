## Best Practices

1. Focus on specific allocation functions from the patch context
2. Handle `unlikely(!ptr)` as valid null checks
3. Track pointer aliasing across assignments
4. Use custom ProgramState maps for tracking
5. Keep checker logic path-sensitive
