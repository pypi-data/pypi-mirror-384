The python boutpp module
========================

Installing
----------

Installing boutpp can be tricky, however in most cases it should be
automatically enabled if all dependencies are available.
To error out on missing dependencies, explicitly enable it::

.. code-block:: bash

   cmake -DBOUT_ENABLE_PYTHON=ON


It can be especially tricky if you want to run boutpp on login nodes
for simple post processing, but due to differences in the instruction
set the compiled modules for the compute nodes do not run there. In
that case you need to manually install all needed dependencies.  It is
probably a good idea to use a different build directory, to not
unintentionally modify your BOUT++ compilation for the compute nodes.

If you are running fedora - you can install pre-build binaries:

.. code-block:: bash

   sudo dnf install python3-bout++-mpich
   module load mpi/mpich-$(arch)

You can also pip install boutpp with:

.. code-block:: bash

   pip install boutpp-nightly

This will download the latest boutpp-nightly version, compile and
install it. Note that you still need all the non-python dependencies
like mpi. Note that after ``pip install boutpp-nightly`` the
``boutpp`` module is installed, so you can use ``import boutpp``
independent of the version used.

After the 5.0.0 release you will also be able to install the latest
released version of boutpp with:

.. code-block:: bash

   pip install boutpp



Purpose
-------

The boutpp module exposes (part) of the BOUT++ C++ library to python.
It allows to calculate e.g. BOUT++ derivatives in python.

State ----- Field3D and Field2D are working. If other fields are
needed, please open an issue.  Fields can be accessed directly using
the [] operators, similar to numpy.  The get all data, ``f3d[:]`` is
equivalent to ``f3d[:, :, :]`` and returns a numpy array.  This array
can be addressed with e.g. ``[]`` operators, and then the field can be
set again with ``f3d[:] = numpyarray``.  It is also possible to set a
part of an Field3D with the ``[]`` operators.  Addition,
multiplication etc. are all available.  The derivatives should all be
working, if find a missing one, please open an issue.

Note that views are currently not supported, thus ``f3d[:] += 1`` will
modify the returned copy, and the ``f3d`` object will be unchanged.

Functions
---------

See the API documentation :ref:`boutpp_api`

Examples
--------
Some trivial post processing:

.. code-block:: python

   import boutpp
   import numpy as np
   args="-d data -f BOUT.settings -o BOUT.post"
   boutpp.init(args)
   dens = boutpp.Field3D.fromCollect("n", path="data")
   temp = boutpp.Field3D.fromCollect("T", path="data")
   pres = dens * temp
   dpdz = boutpp.DDZ(pres, outloc="CELL_ZLOW")



A simple MMS test:

.. code-block:: python

   import boutpp
   import numpy as np
   boutpp.init("-d data -f BOUT.settings -o BOUT.post")
   for nz in [64, 128, 256]:
       boutpp.setOption("meshz:nz", "%d"%nz)
       mesh = boutpp.Mesh(OptionSection="meshz")
       f = boutpp.create3D("sin(z)", mesh)
       sim = boutpp.DDZ(f)
       ana = boutpp.create3D("cos(z)", mesh)
       err = sim - ana
       err = boutpp.max(boutpp.abs(err))
       errors.append(err)


A real example - unstagger data:

.. code-block:: python

   import boutpp
   boutpp.init("-d data -f BOUT.settings -o BOUT.post")
   # uses location from dump - is already staggered
   upar = boutpp.Field3D.fromCollect("Upar")
   upar = boutpp.interp_to(upar, "CELL_CENTRE")
   # convert to numpy array
   upar = upar[:]


A real example - check derivative contributions:

.. code-block:: python

   #!/usr/bin/env python

   from boutpp import *
   import numpy as np
   from netCDF4 import Dataset
   import sys

   if len(sys.argv)> 1:
       path=sys.argv[1]
   else:
       path="data"

   times=collect("t_array",path=path)

   boutpp.init("-d data -f BOUT.settings -o BOUT.post")
   with Dataset(path+'/vort.nc', 'w', format='NETCDF4') as outdmp:
      phiSolver=Laplacian()
      phi=Field3D.fromCollect("n",path=path,tind=0,info=False)
      zeros=phi.getAll()*0
      phi.setAll(zeros)
      outdmp.createDimension('x',zeros.shape[0])
      outdmp.createDimension('y',zeros.shape[1])
      outdmp.createDimension('z',zeros.shape[2])
      outdmp.createDimension('t',None)
      t_array_=outdmp.createVariable('t_array','f4',('t'))
      t_array_[:]=times
      ExB     = outdmp.createVariable('ExB'    ,'f4',('t','x','y','z'))
      par_adv = outdmp.createVariable('par_adv','f4',('t','x','y','z'))
      def setXGuards(phi,phi_arr):
          for z in range(tmp.shape[2]):
              phi[0,:,z]=phi_arr
              phi[1,:,z]=phi_arr
              phi[-2,:,z]=phi_arr
              phi[-1,:,z]=phi_arr
      with open(path+"/equilibrium/phi_eq.dat","rb") as inf:
          phi_arr=np.fromfile(inf,dtype=np.double)
          bm="BRACKET_ARAKAWA_OLD"

          for tind in range(len(times)):
              vort     = Field3D.fromCollect("vort"     ,path=path,tind=tind,info=False)
              U        = Field3D.fromCollect("U"        ,path=path,tind=tind,info=False)
              setXGuards(phi,phi_arr)
              phi=phiSolver.solve(vort,phi)
              ExB[tind,:,:,:]=(-bracket(phi, vort, bm, "CELL_CENTRE")).getAll()
              par_adv[tind,:,:,:]=(- Vpar_Grad_par(U, vort)).getAll()

