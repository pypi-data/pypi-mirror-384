
#pragma once

#include "hipo/utils/Config.hpp"
#include "MultiArch.hpp"
#include <assert.h>
#include <type_traits>


#ifndef HIPO_ENABLE_KOKKOS

#define SPM_LAMBDA [=] SPM_ATTRIBUTE 
#define SPM_INLINE_FUNCTION SPM_ATTRIBUTE
#define SPM_ASSERT(x) assert(x)



namespace hipo {
namespace spm {


bool is_initialized();

void initialize(int argc, char* argv[]);

void finalize();

namespace Impl {
template <class T, class R>
using enable_if_atomic_t =
    std::enable_if_t<!std::is_reference_v<T> && !std::is_const_v<T>,
                     std::remove_volatile_t<R>>;
}  // namespace Impl

}
}


#include "Range.hpp"
#include "Reducer.hpp"


#include "impls/OpenMP.hpp"
#if defined(SPM_ENABLE_CUDA) && defined(__CUDACC__)
#include "impls/Cuda.hpp"
#endif
#if defined(SPM_ENABLE_HIP) && defined(__HIPCC__)
#include "impls/HIP.hpp"
#endif
#if defined(SPM_ENABLE_MUXI) && defined(__MXCC__)
#include "impls/MUXI.hpp"
#endif



#else
// use kokkos as backend programing model
#include <Kokkos_Core.hpp>

namespace hipo {
namespace spm {

#define SPM_LAMBDA KOKKOS_LAMBDA
#define SPM_INLINE_FUNCTION KOKKOS_INLINE_FUNCTION
#define SPM_ASSERT(x) KOKKOS_ASSERT(x)
#if defined(KOKKOS_ENABLE_OPENMP)
#define SPM_ENABLE_OPENMP
#endif
#if defined(KOKKOS_ENABLE_CUDA)
#define SPM_ENABLE_CUDA
using Kokkos::Cuda;
#endif
#if defined(KOKKOS_ENABLE_HIP)
#define SPM_ENABLE_HIP
using Kokkos::HIP;
#endif

        using Kokkos::is_initialized;
        using Kokkos::initialize;
        using Kokkos::finalize;
        using Kokkos::parallel_for;
        using Kokkos::parallel_reduce;
        using Kokkos::RangePolicy;
        using Kokkos::MDRangePolicy;

        using Kokkos::Max;
        using Kokkos::Min;
        using Kokkos::Sum;

        using Kokkos::OpenMP;
        //using Kokkos::Cuda;
        //using Kokkos::HIP;
        template <class Space>
        using RangePolicy2d = Kokkos::MDRangePolicy<Space, Kokkos::Rank<2>>;
}
}



#endif


