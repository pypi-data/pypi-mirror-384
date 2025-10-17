#pragma once
#include "../Range.hpp"
#include <algorithm>
#include <vector>
#include <iostream>

#ifdef SPM_ENABLE_OPENMP
#include <omp.h>
#endif

namespace hipo {
namespace spm {

class OpenMP {
    int nthreads = 1;
public:
    OpenMP() {
#ifdef SPM_ENABLE_OPENMP
    #pragma omp parallel
    nthreads = omp_get_max_threads();
#endif
    }
    int getNumThreads() const {
        return nthreads;
    }
    template <class T>
    SPM_ATTRIBUTE inline static Impl::enable_if_atomic_t<T, T> atomic_fetch_add(T* ptr, T val) {
        T tmp;
        #pragma omp atomic capture
        { tmp = *ptr; *ptr += val; }
        return tmp;
    }
    template <class T>
    SPM_ATTRIBUTE inline static Impl::enable_if_atomic_t<T, void> atomic_add(T* ptr, T val) {
        T tmp;
        #pragma omp atomic capture
        { tmp = *ptr; *ptr += val; }
    }
};

template <class Functor>
void parallel_for(const RangePolicy<OpenMP>& policy, const Functor& functor) {
    int64_t nGlobal = policy.end-policy.begin;
    if (nGlobal <= 0) {
        return;
    }
    int64_t nPart = policy.getParts();
    //std::cout << "parallel_for the nthreads is " << nPart << std::endl;
#ifdef SPM_ENABLE_OPENMP
    #pragma omp parallel for num_threads(nPart)
#endif
    for (int64_t i=0; i<nPart; i++) {
        int64_t begin, end;
        spm_get_start_end(i, nPart, nGlobal, &begin, &end);
        for (int64_t k=begin; k<end; k++) {
            functor(k+policy.begin);
        }
    }
}

template <class Functor>
void parallel_for_part(const RangePolicy<OpenMP>& policy, const Functor& functor) {
    int64_t nGlobal = policy.end-policy.begin;
    int64_t nPart = policy.getParts();
    //std::cout << "parallel_for the nthreads is " << nPart << std::endl;
#ifdef SPM_ENABLE_OPENMP
    #pragma omp parallel for num_threads(nPart)
#endif
    for (int64_t i=0; i<nPart; i++) {
        int64_t begin, end;
        spm_get_start_end(i, nPart, nGlobal, &begin, &end);
        
        functor(nPart, i, policy.begin+begin, policy.begin+end);
    }
}


template <class Functor, class OpT>
void parallel_reduce(const RangePolicy<OpenMP>& policy, const Functor& functor, const OpT& op) {
    typedef typename OpT::value_type ValT;

    int64_t nGlobal = policy.end-policy.begin;
    if (nGlobal <= 0) {
        op.value = op.init;
        return;
    }
    int64_t nPart = policy.space.getNumThreads();
    nPart = std::min(nPart, nGlobal);

    std::vector<ValT> valn(nPart, op.init);
#ifdef SPM_ENABLE_OPENMP
    #pragma omp parallel for num_threads(nPart)
#endif
    for (int64_t i=0; i<nPart; i++) {
        int64_t begin, end;
        spm_get_start_end(i, nPart, nGlobal, &begin, &end);
        for (int64_t k=begin; k<end; k++) {
            functor(k+policy.begin, valn[i]);
        }
    }
    


    op.value = valn[0];
    for (int i=1; i<nPart; i++) {
        op.reduce(valn[i], op.value, op.value);
    }
}


}

}
