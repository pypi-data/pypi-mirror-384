#pragma once

#include "hipo/operators/ParOperator.hpp"

namespace hipo {

template <class _ValT, class _GlobalIdxT, class _LocalIdxT>
class SolverSYMMLQ_T : public ParSolverT<_ValT, _GlobalIdxT, _LocalIdxT> {
    

public:
    SolverSYMMLQ_T();

    void setup(const ParMatrixFreeT<_ValT, _GlobalIdxT, _LocalIdxT> &A) {}

    int create(const JsonValue &params) {
        ParSolverT<_ValT, _GlobalIdxT, _LocalIdxT>::create(params, "SYMMLQ");
        return 0;
    }

    void solve(ParPreconditionerT<_ValT, _GlobalIdxT, _LocalIdxT> &P,
               ParMatrixFreeT<_ValT, _GlobalIdxT, _LocalIdxT> &A,
               const ParMatrixT<_ValT, _GlobalIdxT, _LocalIdxT> &b,
               ParMatrixT<_ValT, _GlobalIdxT, _LocalIdxT> &x, int &iter,
               double &relres);
};

} // namespace hipo
