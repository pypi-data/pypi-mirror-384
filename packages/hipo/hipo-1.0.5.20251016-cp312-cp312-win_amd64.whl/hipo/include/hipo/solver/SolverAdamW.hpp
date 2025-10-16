#pragma once

#include "hipo/operators/ParOperator.hpp"

namespace hipo {

template <class _ValT, class _GlobalIdxT, class _LocalIdxT>
class SolverAdamW_T : public ParSolverT<_ValT, _GlobalIdxT, _LocalIdxT> {

protected:
    typedef typename TypeInfo<_ValT>::scalar_type RealType;

    RealType learning_rate = 0.001;
    RealType beta1 = 0.9;
    RealType beta2 = 0.99;
    RealType epsilon = 1e-8;
    RealType weight_decay = 0.01;
    bool amsgrad = false;
    bool maximize = false;

public:
    SolverAdamW_T();

    void setup(const ParMatrixFreeT<_ValT, _GlobalIdxT, _LocalIdxT> &A) {}

    int create(const JsonValue &params) {
        ParSolverT<_ValT, _GlobalIdxT, _LocalIdxT>::create(params, "AdamW");
        FACTORY_GET_JSON_VAL(learning_rate, "learning_rate", RealType);
        FACTORY_GET_JSON_VAL(beta1, "beta1", RealType);
        FACTORY_GET_JSON_VAL(beta2, "beta2", RealType);
        FACTORY_GET_JSON_VAL(epsilon, "epsilon", RealType);
        FACTORY_GET_JSON_VAL(weight_decay, "weight_decay", RealType);
        FACTORY_GET_JSON_VAL(amsgrad, "amsgrad", bool);
        FACTORY_GET_JSON_VAL(maximize, "maximize", bool);

        return 0;
    }

    void solve(ParPreconditionerT<_ValT, _GlobalIdxT, _LocalIdxT> &P,
               ParMatrixFreeT<_ValT, _GlobalIdxT, _LocalIdxT> &A,
               const ParMatrixT<_ValT, _GlobalIdxT, _LocalIdxT> &b,
               ParMatrixT<_ValT, _GlobalIdxT, _LocalIdxT> &x, int &iter,
               double &relres);
};

} // namespace hipo
