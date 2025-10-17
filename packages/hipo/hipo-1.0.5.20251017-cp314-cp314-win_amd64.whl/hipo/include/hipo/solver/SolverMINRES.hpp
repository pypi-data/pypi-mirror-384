#pragma once

#include "hipo/operators/ParOperator.hpp"

namespace hipo {

template <class _ValT, class _GlobalIdxT, class _LocalIdxT>
class SolverMINRES_T : public ParSolverT<_ValT, _GlobalIdxT, _LocalIdxT> {
    std::string  algo = "qlp";
    int norm_type = 2;
    int monitor = 0;
    int qlp = 1;
    double radius = 0;

public:
    SolverMINRES_T();

    void setup(const ParMatrixFreeT<_ValT, _GlobalIdxT, _LocalIdxT> &A) {}

    int create(const JsonValue &params) {
        ParSolverT<_ValT, _GlobalIdxT, _LocalIdxT>::create(params, "MINRES");
        FACTORY_GET_JSON_VAL(algo, "algo", std::string);
        FACTORY_GET_JSON_VAL(monitor, "monitor", int);
        FACTORY_GET_JSON_VAL(norm_type, "norm_type", int);
        FACTORY_GET_JSON_VAL(qlp, "qlp", int);
        FACTORY_GET_JSON_VAL(radius, "radius", double);

        return 0;
    }

    void solve(ParPreconditionerT<_ValT, _GlobalIdxT, _LocalIdxT> &P,
               ParMatrixFreeT<_ValT, _GlobalIdxT, _LocalIdxT> &A,
               const ParMatrixT<_ValT, _GlobalIdxT, _LocalIdxT> &b,
               ParMatrixT<_ValT, _GlobalIdxT, _LocalIdxT> &x, int &iter,
               double &relres);
};

} // namespace hipo
