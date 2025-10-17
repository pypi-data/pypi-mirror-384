#g++ proxy_mpi.cpp -o libproxy_mpi.so -shared -fPIC -fno-rtti -fno-exceptions -DPROXY_MPI_DUMMY_IMPL
mpicxx proxy_mpi.cpp -o libproxy_mpi.so -shared -O3 -fPIC -fno-rtti -fno-exceptions -std=c++11 -Wl,-z,defs,--as-needed
