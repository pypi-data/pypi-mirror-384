#pragma once

#include "hipo/operators/ParOperator.hpp"

namespace hipo {
template <class _ValT, class _GlobalIdxT, class _LocalIdxT>
class ParSolverGMRES_T : public ParSolverT<_ValT, _GlobalIdxT, _LocalIdxT> {
public:
    int Restart = 10;
    int MaxIters = 500;
    double Tolerance = 1.0e-08;
    int PrintStats = 0;

    ParSolverGMRES_T();

    int create(const JsonValue &params) {
        FACTORY_GET_JSON_VAL(Restart, "restart", int);
        FACTORY_GET_JSON_VAL(MaxIters, "max_iters", int);
        FACTORY_GET_JSON_VAL(Tolerance, "tolerance", double);
        FACTORY_GET_JSON_VAL(PrintStats, "print_stats", int);
        return 0;
    }

	void setup(const ParMatrixFreeT<_ValT, _GlobalIdxT, _LocalIdxT> &A) {}

    void solve(ParPreconditionerT<_ValT, _GlobalIdxT, _LocalIdxT> &P,
               ParMatrixFreeT<_ValT, _GlobalIdxT, _LocalIdxT> &A,
               const ParMatrixT<_ValT, _GlobalIdxT, _LocalIdxT> &b,
               ParMatrixT<_ValT, _GlobalIdxT, _LocalIdxT> &x, int &iter,
               double &relres);
};

} // namespace hipo

