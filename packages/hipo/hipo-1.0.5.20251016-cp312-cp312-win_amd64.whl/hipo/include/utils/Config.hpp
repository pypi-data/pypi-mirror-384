#pragma once

#define HIPO_ENABLE_MPI
/* #undef HIPO_ENABLE_GLOG */
#define HIPO_ENABLE_HYPRE
#define HIPO_ENABLE_PYTHON
/* #undef HIPO_ENABLE_AMGCL */
/* #undef HIPO_ENABLE_KOKKOS */
/* #undef HIPO_ENABLE_MUMPS */
/* #undef HIPO_ENABLE_GTEST */

/* #undef SPM_ENABLE_OPENMP */
/* #undef HIPO_ENABLE_OPENMP */

#define SPM_ENABLE_CUDA
#define HIPO_ENABLE_CUDA

/* #undef SPM_ENABLE_HIP */
/* #undef HIPO_ENABLE_HIP */


#if defined (_WIN64) || defined (WIN32) || defined (_WIN32)

#ifdef hipo_EXPORTS
#define HIPO_WIN_API __declspec(dllexport)
#else
//#define HIPO_WIN_API __declspec(dllimport)
#define HIPO_WIN_API
#endif

#else

#define HIPO_WIN_API

#endif
