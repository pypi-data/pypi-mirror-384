#pragma once

#include "hipo/operators/ParOperator.hpp"

namespace hipo {

template <class _ValT, class _GlobalIdxT, class _LocalIdxT, class _PValT=_ValT>
class SolverFLGMRES_R_T : public ParSolverT<_ValT, _GlobalIdxT, _LocalIdxT> {
    //int max_its = 1000;
    //double rtol = 1e-8;
    double btol = 0;
    double atol = 0;
    int restart = 20;
    int augk = 2;
    int verb = 0;

public:
    SolverFLGMRES_R_T();

    void setup(const ParMatrixFreeT<_ValT, _GlobalIdxT, _LocalIdxT> &A) {}

    int create(const JsonValue &params) {
        ParSolverT<_ValT, _GlobalIdxT, _LocalIdxT>::create(params, "FLGMRES_R");
        //FACTORY_GET_JSON_VAL(max_its, "max_its", int);
        //FACTORY_GET_JSON_VAL(rtol, "rtol", double);
        FACTORY_GET_JSON_VAL(btol, "btol", double);
        FACTORY_GET_JSON_VAL(atol, "atol", double);
        FACTORY_GET_JSON_VAL(restart, "restart", int);
        FACTORY_GET_JSON_VAL(augk, "augk", int);
        FACTORY_GET_JSON_VAL(verb, "verb", int);
        return 0;
    }

    void solve(ParPreconditionerT<_PValT, _GlobalIdxT, _LocalIdxT> &P,
               ParMatrixFreeT<_ValT, _GlobalIdxT, _LocalIdxT> &A,
               const ParMatrixT<_ValT, _GlobalIdxT, _LocalIdxT> &b,
               ParMatrixT<_ValT, _GlobalIdxT, _LocalIdxT> &x, int &iter,
               double &relres);
};

} // namespace hipo
