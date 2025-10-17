#pragma once
#include <stdio.h>
#include <hip/hip_runtime.h>
#include "../Range.hpp"
#include "hipo/utils/Complex.hpp"


namespace hipo {
namespace spm {

#define HIP_CHECK(command) do { hipError_t status = command; if (status != HIP_SUCCESS) { printf("HIP CHECK FAIL '%s', error '%s' file %s line %d\n", #command, hipGetErrorString(status), __FILE__, __LINE__); }} while (0)

struct HIP {
    hipStream_t stream = 0;
    hipDeviceProp_t prop;
    bool managed = true;
    int deviceId = 0;
public:
    //HIP() {}
    HIP(hipStream_t stream, bool managed = true) {
        this->stream = stream;
        this->managed = managed;
        HIP_CHECK(hipGetDevice(&this->deviceId));
        HIP_CHECK(hipGetDeviceProperties(&prop, this->deviceId));
    }
    ~HIP() {
        if (managed && stream != 0) {
            hipError_t ret = hipStreamDestroy(stream);
        }
    }
    hipStream_t getStream() const {
        return stream;
    }
    // 可以支持不同的卡，不同的卡的线程数不一样。需要动态支持。
    int getThreadsPerBlock() const {
        return prop.maxThreadsPerBlock;
    }
    int getTotalThreads() const {
        return prop.multiProcessorCount*prop.maxThreadsPerMultiProcessor;
    }
    int getBlocks(int N) const {
        int num_threads = getThreadsPerBlock();
        return (N + num_threads - 1) / num_threads;
    }
    template <class T>
    SPM_ATTRIBUTE inline static Impl::enable_if_atomic_t<T, T> atomic_fetch_add(T* ptr, T val) {
        if constexpr (std::is_same<T, float>::value || std::is_same<T, double>::value) {
            return ::atomicAdd(ptr, val);
        } else if constexpr (std::is_same<T, int32_t>::value) {
            return ::atomicAdd(ptr, val);
        } else if constexpr (std::is_same<T, int64_t>::value) {
            typedef unsigned long long int ULLI;
            static_assert(sizeof(ULLI) == sizeof(T), "int64_t not equal to ULLI");
            return ::atomicAdd((ULLI*)ptr, (ULLI)val);
        } else {
            return T();
        }
    }
    template <class T>
    SPM_ATTRIBUTE inline static Impl::enable_if_atomic_t<T, void> atomic_add(T* ptr, T val) {
        if constexpr (std::is_same<T, float>::value || std::is_same<T, double>::value) {
            ::atomicAdd(ptr, val);
        } else if constexpr (std::is_same<T, int32_t>::value) {
            ::atomicAdd(ptr, val);
        } else if constexpr (std::is_same<T, int64_t>::value) {
            typedef unsigned long long int ULLI;
            static_assert(sizeof(ULLI) == sizeof(T), "int64_t not equal to ULLI");
            ::atomicAdd((ULLI*)ptr, (ULLI)val);
        }
    }
};

#define SPM_HIP_KERNEL_LOOP(i, n) \
  for (int i = blockIdx.x * blockDim.x + threadIdx.x; \
       i < (n); \
       i += blockDim.x * gridDim.x)



template <typename Functor>
__global__ void spmKernelFor(int64_t nPart, int64_t gBegin, int64_t gEnd, Functor functor) {
    int64_t i = threadIdx.x + blockIdx.x * blockDim.x;
    if (i >= nPart) {
        return;
    }
    int64_t nGlobal = gEnd-gBegin;
    int64_t begin, end;
    spm_get_start_end(i, nPart, nGlobal, &begin, &end);
    //printf("spm kernel npart %ld, i %ld, global %ld, begin %ld, end %ld\n", nPart, i, nGlobal, begin, end);
    for (int64_t k=begin; k<end; k++) {
        functor(k+gBegin);
    }
}

template <class Functor>
void parallel_for(const RangePolicy<HIP>& policy, const Functor& functor) {
    int64_t nGlobal = policy.end-policy.begin;
    if (nGlobal <= 0) {
        return;
    }
    //int64_t nPart = nGlobal;
    int64_t nPart = policy.space.getTotalThreads();
    //printf("spm parallel_for npart %ld, i %ld, global %ld, begin %ld, end %ld\n", nPart, 0L, nGlobal, policy.begin, policy.end);
    hipStream_t stream = policy.space.getStream();
    spmKernelFor<<<policy.space.getBlocks(nPart), policy.space.getThreadsPerBlock(), 0, stream>>>(nPart, policy.begin, policy.end, functor);
    HIP_CHECK(hipStreamSynchronize(stream));
}

template <typename Functor, typename OpT>
__global__ void spmKernelReduce(int64_t nPart, int64_t gBegin, int64_t gEnd, Functor functor, typename OpT::value_type* partial_reduce, OpT op) {

    int64_t i = threadIdx.x + blockIdx.x * blockDim.x;
    if (i >= nPart) {
        return;
    }
    typedef typename OpT::value_type ValT;
    int64_t begin, end;
    int64_t nGlobal = gEnd-gBegin;
    spm_get_start_end(i, nPart, nGlobal, &begin, &end);
    //printf("spm kernel npart %ld, i %ld, global %ld, begin %ld, end %ld\n", nPart, i, nGlobal, begin, end);
    ValT tmp = op.init;
    for (int64_t k=begin; k<end; k++) {
        functor(k+gBegin, tmp);
    }
    partial_reduce[i] = tmp;
}

template <typename OpT>
__global__ void spmKernelReduceSmallArray(int N, typename OpT::value_type* array, OpT op) {
    typedef typename OpT::value_type ValT;
    ValT ret = array[0];
    for (int i=1; i<N; i++) {
        op.reduce(ret, array[i], ret);
    }
    array[0] = ret;
}

template <class Functor, class OpT>
void parallel_reduce(const RangePolicy<HIP>& policy, const Functor& functor, const OpT& op) {
    typedef typename OpT::value_type ValT;
    int64_t nGlobal = policy.end-policy.begin;
    if (nGlobal <= 0) {
        op.value = op.init;
        return;
    }
    int REDUCE_LEN = 256;
    int nPart = nGlobal > REDUCE_LEN ? REDUCE_LEN : nGlobal;

    hipStream_t stream = policy.space.getStream();
    ValT* partial_reduce = 0;

    HIP_CHECK(hipMallocAsync(&partial_reduce, sizeof(ValT)*nPart, stream));
    if (0 == partial_reduce) {
        printf("hip can not alloc memory for stream %p\n", stream);
        return;
    }

    /// to be optimized
    spmKernelReduce<<<policy.space.getBlocks(nPart), policy.space.getThreadsPerBlock(), 0, stream>>>(nPart, policy.begin, policy.end, functor, partial_reduce, op);
    spmKernelReduceSmallArray<<<1, 1, 0, stream>>>(nPart, partial_reduce, op);

    HIP_CHECK(hipMemcpyAsync(&op.value, partial_reduce, sizeof(ValT),  hipMemcpyDeviceToHost, stream));
    HIP_CHECK(hipFreeAsync(partial_reduce, stream));
    HIP_CHECK(hipStreamSynchronize(stream));

}


}

}
