#ifndef FAKESOLVER_H
#define FAKESOLVER_H

#include "gtest/gtest.h"

#include "bout/solver.hxx"

#include <algorithm>
#include <string>
#include <vector>

class FakeSolver : public Solver {
public:
  FakeSolver(Options* options) : Solver(options) { has_constraints = true; }
  ~FakeSolver() = default;

  int run() override {
    run_called = true;
    if ((*options)["throw_run"].withDefault(false)) {
      throw BoutException("Deliberate exception in FakeSolver::run");
    }
    return (*options)["fail_run"].withDefault(0);
  }
  bool run_called{false};

  int init() override {
    init_called = true;
    Solver::init();
    return (*options)["fail_init"].withDefault(0);
  }
  bool init_called{false};

  void changeHasConstraints(bool new_value) { has_constraints = new_value; }

  auto listField2DNames() -> std::vector<std::string> {
    std::vector<std::string> result{};
    std::transform(begin(f2d), end(f2d), std::back_inserter(result),
                   [](const VarStr<Field2D>& f) { return f.name; });
    return result;
  }

  auto listField3DNames() -> std::vector<std::string> {
    std::vector<std::string> result{};
    std::transform(begin(f3d), end(f3d), std::back_inserter(result),
                   [](const VarStr<Field3D>& f) { return f.name; });
    return result;
  }

  auto listVector2DNames() -> std::vector<std::string> {
    std::vector<std::string> result{};
    std::transform(begin(v2d), end(v2d), std::back_inserter(result),
                   [](const VarStr<Vector2D>& f) { return f.name; });
    return result;
  }

  auto listVector3DNames() -> std::vector<std::string> {
    std::vector<std::string> result{};
    std::transform(begin(v3d), end(v3d), std::back_inserter(result),
                   [](const VarStr<Vector3D>& f) { return f.name; });
    return result;
  }

  // Shims for protected functions
  auto getMaxTimestepShim() const -> BoutReal { return max_dt; }
  using Solver::call_monitors;
  using Solver::call_timestep_monitors;
  using Solver::getLocalN;
  using Solver::getMonitors;
  using Solver::globalIndex;
  using Solver::hasJacobian;
  using Solver::hasPreconditioner;
  using Solver::MonitorInfo;
  using Solver::runJacobian;
  using Solver::runPreconditioner;
};

// Equality operator for tests
inline bool operator==(const FakeSolver::MonitorInfo& lhs,
                       const FakeSolver::MonitorInfo& rhs) {
  return lhs.monitor == rhs.monitor and lhs.time_dimension == rhs.time_dimension;
}

#endif // FAKESOLVER_H
