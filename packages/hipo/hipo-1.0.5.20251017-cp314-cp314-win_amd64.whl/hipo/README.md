# High performance Intelligent Preconditioning Operators

## Introduction

HIPO, short for High performance Intelligent Preconditioning Operators, is a large-scale linear equation solver package. It supports distributed heterogeneous parallel computing (MPI+CPU/GPU/DCU/...) and provides physics-informed preconditioners for solvers, especially physics-informed AMG preconditioners. It is dedicated to stably and efficiently solving large-scale linear algebraic equations derived from the discretization of mathematical and physical models.

## Install

``` bash
$ pip install hipo
```

## Usage
use the following command to get the help message:
```bash
$ python -m hipo help
```
copy the example out
```
$ export HIPO_PATH=path_to_hipo
$ cp -r $HIPO_PATH/examples .
```
then run the example:
```bash
$ python solver.py -fnA thermal1.mtx -fnb thermal1_b.mtx solver.json -device cuda:0
```
to run the distributed verison,
```bash

# solve the laplace equation defined by testcase in solver.json
$ $HIPO_PATH/bin/mpirun -n 2 python solver.py solver.json -device cpu

# solve the equation in matrix market format
$ $HIPO_PATH/bin/mpirun -n 2 python solver.py -fnA thermal1.mtx -fnb thermal1_b.mtx solver.json -device cuda:0

```

The following python script shows the above solver.py.
read matrix A and vector b from MatrixMarket files,
using CUDA to solve Ax=b.
```python
# solver.py
import hipo
import sys, re, os
#import json
import commentjson as json

fnA = sys.argv[1]
fnb = sys.argv[2]
config = sys.argv[3]

params = json.load(open(config))

A = hipo.ParCSRMatrix()
A.loadFromFile(fnA)
b = hipo.ParMatrix()
b.loadFromFile(fnb)
if b.getSize() == 0:
    b.resize(A.getRows(), 1)
    b.fill(1)

# transfer the matrix and vector to gpu 0.
dev = hipo.Device("cuda:0")
A = A.toDevice(dev)
b = b.toDevice(dev)

# use gpu 0 to finish the computation.
precond = hipo.createPrecond(params["preconditioner"])
precond.setup(A)
solver = hipo.createSolver(params["solver"])
solver.setup(A)

out = solver.solve(precond, A, b)
```

## Solvers and Preconditioners
use
```bash
$ python -m hipo info
```
to show the builtin solvers, preconditioners, smoothers, level_transfers.


## Compatibility
- ### OS version
HIPO support Linux, Windows.  MacOS version will be available later.

- ### PYTHON version
HIPO support python version 3.8, 3.9, 3.10, 3.11, 3.12, 3.13, 3.14. 

- ### GPU/CUDA version
HIPO support NVIDIA GPU, with CUDA Version >= 12.4. 

- ### DCU version
please contact us to compile the specified version.

- ### DISTRIBUTED version
hipo is compiled with MPICH on linux, and MSMPI on windows. HIPO does not depend on vendor MPI directly, 
but depends on MPI-proxy called proxy_mpi, which is a binary compatible implementation for certern MPI versions.
so you can use you own MPI by compile the proxy_mpi for your MPI version:
```
$ cd $HIPO_PATH/mpi-src
$ bash build.sh
$ cp libhipo_mpi.so $HIPO_PATH/lib/
```


## License

This software is free software distributed under the Lesser General Public 
License or LGPL, version 3.0 or any later versions. This software distributed 
in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even 
the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. 
See the GNU Lesser General Public License for more details.

You should have received a copy of the GNU Lesser General Public License 
along with HIPO. If not, see <http://www.gnu.org/licenses/>.

This software optionally depends on HYPRE, their license files are located in the package.
