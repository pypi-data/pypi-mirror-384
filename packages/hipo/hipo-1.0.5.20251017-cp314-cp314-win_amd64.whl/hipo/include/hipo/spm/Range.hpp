#pragma once

#include "MultiArch.hpp"
#include <cstdint>

namespace hipo {
namespace spm {

template <class Space>
class RangePolicy {
public:
    Space& space;
    int64_t begin = 0;
    int64_t end = 0;
    int64_t npart = -1;
    RangePolicy(Space& s, int64_t b, int64_t e, int64_t p=-1): space(s), begin(b), end(e), npart(p) {}
    int64_t getParts() const {
        int64_t nGlobal = end-begin;
        int64_t nPart = space.getNumThreads();
        nPart = std::min(nPart, nGlobal);
        if (npart > 0) {
            nPart = std::min(nPart, npart);
        }
        return nPart;
    }
};



template <class _IntT>
SPM_ATTRIBUTE void spm_get_start_end (const _IntT  procid,
                         const _IntT  nprocs,
                         const _IntT  n,
                         _IntT       *start,
                         _IntT       *end)
{
    _IntT chunk_size = n / nprocs;
    _IntT mod =  n % nprocs;
    _IntT start_loc, end_loc;
    
    if ( procid < mod) {
        end_loc = chunk_size + 1;
        start_loc = end_loc * procid;
    }
    else {
        end_loc = chunk_size;
        start_loc = end_loc * procid + mod;
    }
    end_loc = end_loc + start_loc;
    
    *start = start_loc;
    *end = end_loc;
}


}
}
