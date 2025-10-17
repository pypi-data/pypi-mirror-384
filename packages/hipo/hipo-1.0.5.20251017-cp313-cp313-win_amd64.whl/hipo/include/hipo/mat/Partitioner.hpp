#pragma once
#include <memory>
#include "hipo/comm/smpi.hpp"
#include "hipo/spm/Range.hpp"
#include "hipo/comm/communication_tools.h"
#include "Matrix_fwd.hpp"

namespace hipo {

template <class _GlobalIdxT, class _LocalIdxT>
class HIPO_WIN_API PartitionerT {
public:
    PartitionerT();
    void create(_GlobalIdxT global_size, _LocalIdxT nparts);
    void create(_GlobalIdxT global_size, const std::vector<_GlobalIdxT>& partlist);

    void getOwnerShipRangeForPart(_LocalIdxT partId, _GlobalIdxT* p_start, _GlobalIdxT* p_end) const;
    void global2Local(_GlobalIdxT globalIndex, _LocalIdxT& partIdx, _LocalIdxT& localIndex) const;
    _LocalIdxT getLocalSizeForPart(_LocalIdxT partId) const;

    MatrixT<_LocalIdxT, _LocalIdxT> getPartition() const;
    int getNumParts() const;
    _GlobalIdxT getGlobalSize() const;

    bool operator == (const PartitionerT& p2) const;
    bool operator != (const PartitionerT& p2) const;

    static _GlobalIdxT firstGreaterOrEqual(const std::vector<_GlobalIdxT>& arr, _GlobalIdxT num);

protected:
    struct PartitionImpl;
    std::shared_ptr<PartitionImpl> m_impl;
};
    
    } // namespace hipo
