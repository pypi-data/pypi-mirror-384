/// Finite Volume parallel diffusion example
///

#include <bout/fv_ops.hxx>
#include <bout/physicsmodel.hxx>

class Diffusion : public PhysicsModel {
protected:
  int init(bool UNUSED(restarting)) override {
    GRID_LOAD(k);
    mesh->communicate(k);

    SOLVE_FOR(f);

    return 0;
  }

  int rhs(BoutReal UNUSED(time)) override {
    mesh->communicate(f);

    ddt(f) = FV::Div_par_K_Grad_par(k, f);

    return 0;
  }

private:
  Field3D f; // Evolving field
  Field3D k; // Diffusion coefficient
};

BOUTMAIN(Diffusion);
