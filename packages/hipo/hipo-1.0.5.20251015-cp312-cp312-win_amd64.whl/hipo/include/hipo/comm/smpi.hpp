#pragma once

#include "hipo/utils/Config.hpp"

#ifdef HIPO_ENABLE_MPI

//#warning use external mpi
#if HIPO_ENABLE_HIPO_MPI
#define HIPO_MPI_IMPORTS
#include "hipo_mpi.hpp"
#else
#include <mpi.h>
#endif

#else

#include "serial_mpi.hpp"

#endif
