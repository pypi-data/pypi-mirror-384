#pragma once

#include "hipo/utils/Config.hpp"

#if defined(__CUDACC__) || defined(__HIPCC__) || defined(__MXCC__)
#define SPM_ATTRIBUTE __host__ __device__
//#warning device host are all supported
#else
#define SPM_ATTRIBUTE
#endif




