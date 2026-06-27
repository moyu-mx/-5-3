## Checker Template Structure

```cpp
namespace {
class NewChecker : public Checker<{{Callback Functions}}> {
  mutable std::unique_ptr<BugType> BT;
public:
  NewChecker() : BT(new BugType(this, "{{Bug desc}}")) {}
  {{Declaration of Callback Functions}}
private:
  {{Declaration of Self-Defined Functions}}
};
}
REGISTER_CHECKER(NewChecker)
```

## Recommended Callbacks

- `checkPostCall`: Track allocation return values
- `checkBranchCondition`: Detect null checks in branches
- `checkLocation`: Warn on unchecked dereference
- `checkBind`: Handle pointer aliasing
