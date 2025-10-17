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
    mpi_path = os.path.join(hipo_path, 'bin/mpirun')
    if args.subcommand == 'help':
        print(f'''
  use
    export HIPO_PATH={hipo_path}
    cp -r {examples_path} .
  to copy out a example, and use 
    python solver.py thermal1.mtx thermal1_b.mtx solver.json
  to run the example, use
    {mpi_path} -n 2 python solver.py -Afn thermal1.mtx -bfn thermal1_b.mtx solver.json
    {mpi_path} -n 2 python solver.py solver.json
  to run the example with 2 processes.
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

