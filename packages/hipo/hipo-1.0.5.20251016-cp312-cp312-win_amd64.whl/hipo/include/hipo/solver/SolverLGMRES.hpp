#pragma once

#include "hipo/operators/ParOperator.hpp"

namespace hipo {

template <class _ValT, class _GlobalIdxT, class _LocalIdxT>
class SolverLGMRES_T : public ParSolverT<_ValT, _GlobalIdxT, _LocalIdxT> {
    

public:
    SolverLGMRES_T();

    void setup(const ParMatrixFreeT<_ValT, _GlobalIdxT, _LocalIdxT> &A) {}

    int create(const JsonValue &params) {
        ParSolverT<_ValT, _GlobalIdxT, _LocalIdxT>::create(params, "LGMRES");
        return 0;
    }

    void solve(ParPreconditionerT<_ValT, _GlobalIdxT, _LocalIdxT> &P,
               ParMatrixFreeT<_ValT, _GlobalIdxT, _LocalIdxT> &A,
               const ParMatrixT<_ValT, _GlobalIdxT, _LocalIdxT> &b,
               ParMatrixT<_ValT, _GlobalIdxT, _LocalIdxT> &x, int &iter,
               double &relres);
};

} // namespace hipo
