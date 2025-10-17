#pragma once

#include "hipo/operators/ParOperator.hpp"

namespace hipo {

template <class _ValT, class _GlobalIdxT, class _LocalIdxT>
class ParSolverCG_T : public ParSolverT<_ValT, _GlobalIdxT, _LocalIdxT> {
    int MaxIters = 5000;
    double Tolerance = 1e-8;
    int PrintStats = 0;

public:
    ParSolverCG_T();

    void setup(const ParMatrixFreeT<_ValT, _GlobalIdxT, _LocalIdxT> &A) {}

    int create(const JsonValue &params) {
        FACTORY_GET_JSON_VAL(MaxIters, "max_its", int);
        FACTORY_GET_JSON_VAL(Tolerance, "rtol", double);
        FACTORY_GET_JSON_VAL(PrintStats, "verb", int);
        return 0;
    }

    void solve(ParPreconditionerT<_ValT, _GlobalIdxT, _LocalIdxT> &P,
               ParMatrixFreeT<_ValT, _GlobalIdxT, _LocalIdxT> &A,
               const ParMatrixT<_ValT, _GlobalIdxT, _LocalIdxT> &b,
               ParMatrixT<_ValT, _GlobalIdxT, _LocalIdxT> &x, int &iter,
               double &relres);
};

} // namespace hipo
