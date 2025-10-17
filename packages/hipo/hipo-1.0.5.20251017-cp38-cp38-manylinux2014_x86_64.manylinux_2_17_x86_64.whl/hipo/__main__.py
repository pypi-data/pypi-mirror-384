import argparse
import os,sys,re
import hipo

def parse_args():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(title='subcommands', dest='subcommand')
    help_parser = subparsers.add_parser('help', help='show help')
    info_parser = subparsers.add_parser('info', help='show info of the package')
    args = parser.parse_args()
    return parser, args

def main():
    parser, args = parse_args()
    hipo_path = os.path.abspath(os.path.dirname(__file__))
    examples_path = os.path.join(hipo_path, 'examples')
    mpi_path = os.path.join(hipo_path, 'bin', 'mpirun')
    if args.subcommand == 'help':
        print(f'''
  
  1. RUN python
  copy out a example:
    $ export HIPO_PATH={hipo_path}
    $ cp -r {examples_path} .
  1.1 serial run: 
    run the solver on CPU:
      $ python solver.py -Afn thermal1.mtx -bfn thermal1_b.mtx solver.json
    run the solver on GPU 0:
      $ python solver.py -device cuda:0 -Afn thermal1.mtx -bfn thermal1_b.mtx solver.json
  1.2 Distributed run:
    run the example with 2 processes.
      $ {mpi_path} -n 2 python solver.py -Afn thermal1.mtx -bfn thermal1_b.mtx solver.json
      $ {mpi_path} -n 2 python solver.py solver.json

  2. COMPILE
  2.1 Windows
      $ set HIPO_PATH={hipo_path}
      $ cl /utf-8 /EHsc solver.cpp -I%HIPO_PATH%/include -I%HIPO_PATH%/mpi-src %HIPO_PATH%/lib/libhipo.so %HIPO_PATH%/lib/libproxy_mpi.so
  2.2 Linux
      $ export HIPO_PATH={hipo_path}
      $ g++ solver.cpp -I$HIPO_PATH/include -I$HIPO_PATH/mpi-src $HIPO_PATH/lib/libhipo.so $HIPO_PATH/lib/libproxy_mpi.so
  ''')

    elif args.subcommand == 'info':
        print("Devices:")
        for it in hipo.getAllDevices():
          print(f"    {it}")
        for it, lst in hipo.getAllInstances().items():
          print(f"{it}")
          for inst in lst:
            print(f"    {inst}")
    else:
      parser.print_help()
main()

