/*
 * Test of eigenvalue solver in box
 * 
 * Solves wave equation
 *  d^2f/dt^2 = d^2f/dx^2
 */

#include <bout/derivs.hxx>
#include <bout/physicsmodel.hxx>

class EigenBox : public PhysicsModel {
protected:
  int init(bool) override {
    solver->add(f, "f");
    solver->add(g, "g");
    return 0;
  }
  int rhs(BoutReal) override {
    mesh->communicate(f);

    ddt(g) = D2DX2(f);
    ddt(f) = g;

    return 0;
  }

private:
  Field3D f, g;
};

BOUTMAIN(EigenBox);
