#pragma once

#include "hipo/operators/ParOperator.hpp"

namespace hipo {

template <class _PrecondValT, class _ValT, class _GlobalIdxT, class _LocalIdxT>
class ParSolverCG_MP_T : public ParSolverT<_ValT, _GlobalIdxT, _LocalIdxT> {
    int MaxIters = 5000;
    double Tolerance = 1e-8;
    int PrintStats = 0;

public:
    ParSolverCG_MP_T();

    void setup(const ParMatrixFreeT<_ValT, _GlobalIdxT, _LocalIdxT> &A) {}

    int create(const JsonValue &params) {
        FACTORY_GET_JSON_VAL(MaxIters, "max_iters", int);
        FACTORY_GET_JSON_VAL(Tolerance, "tolerance", double);
        FACTORY_GET_JSON_VAL(PrintStats, "print_stats", int);
        return 0;
    }

    void solve(ParPreconditionerT<_PrecondValT, _GlobalIdxT, _LocalIdxT> &P,
               ParMatrixFreeT<_ValT, _GlobalIdxT, _LocalIdxT> &A,
               const ParMatrixT<_ValT, _GlobalIdxT, _LocalIdxT> &b,
               ParMatrixT<_ValT, _GlobalIdxT, _LocalIdxT> &x, int &iter,
               double &relres);

    virtual void solve(ParPreconditionerT<_ValT, _GlobalIdxT, _LocalIdxT> &P,
               ParMatrixFreeT<_ValT, _GlobalIdxT, _LocalIdxT> &A,
               const ParMatrixT<_ValT, _GlobalIdxT, _LocalIdxT> &b,
               ParMatrixT<_ValT, _GlobalIdxT, _LocalIdxT> &x, int &iter,
               double &relres) {
                typedef ParPreconditionerT<_PrecondValT, _GlobalIdxT, _LocalIdxT> NewPrecond;
                NewPrecond* newP = reinterpret_cast<NewPrecond*>(&P);
            solve(*newP, A, b, x, iter, relres);
    }
    virtual void solve(ParMatrixFreeT<_ValT, _GlobalIdxT, _LocalIdxT> &A,
     const ParMatrixT<_ValT, _GlobalIdxT, _LocalIdxT> &b, 
     ParMatrixT<_ValT, _GlobalIdxT, _LocalIdxT> &x,
      int &iter, double &relres) {
        auto P = ParPreconditionerT<_PrecondValT, _GlobalIdxT, _LocalIdxT>::getFactory()->createInstance("Identity");
        this->solve(*P, A, b, x, iter, relres);
    }
};

} // namespace hipo
