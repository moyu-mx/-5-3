// KNighter-synthesized checker for kzalloc null dereference
#include "clang/StaticAnalyzer/Core/BugReporter/BugType.h"
#include "clang/StaticAnalyzer/Core/PathSensitive/CheckerContext.h"

using namespace clang;
using namespace ento;

namespace {
class kzallocNullChecker : public Checker<check::PostStmt<CallExpr>,
                                          check::BranchCondition,
                                          check::Location,
                                          check::Bind> {
  mutable std::unique_ptr<BugType> BT;

public:
  kzallocNullChecker() : BT(new BugType(this, "kzalloc null dereference", "Null Dereference")) {}

  void checkPostCall(const CallEvent &Call, CheckerContext &C) const;
  void checkBranchCondition(const Stmt *Cond, CheckerContext &C) const;
  void checkLocation(SVal Loc, bool IsLoad, const Stmt *S, CheckerContext &C) const;
  void checkBind(SVal Loc, SVal Val, const Stmt *S, CheckerContext &C) const;
};
}

REGISTER_CHECKER(kzallocNullChecker)