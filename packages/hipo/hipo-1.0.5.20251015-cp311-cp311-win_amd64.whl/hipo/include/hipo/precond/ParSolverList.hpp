#pragma once
#include "hipo/operators/ParOperator.hpp"
#include "hipo/mat/ParCSRMatrix.hpp"
#include <vector>


namespace hipo {

template <class _ValT, class _GlobalIdxT, class _LocalIdxT>
class ParSolverList_T: public ParSolverT<_ValT, _GlobalIdxT, _LocalIdxT> {
public:
    

    using MatrixFree = ParMatrixFreeT<_ValT, _GlobalIdxT, _LocalIdxT>;
    using Vector = ParMatrixT<_ValT,  _GlobalIdxT, _LocalIdxT>;
    typedef typename TypeInfo<_ValT>::scalar_type ScalarType;

    using ParSolverT<_ValT, _GlobalIdxT, _LocalIdxT>::rtol;
    using ParSolverT<_ValT, _GlobalIdxT, _LocalIdxT>::max_its;


    std::vector<std::shared_ptr<ParSolverT<_ValT, _GlobalIdxT, _LocalIdxT>>> ops_list;


    int create(const JsonValue& params) {
        ParSolverT<_ValT, _GlobalIdxT, _LocalIdxT>::create(params, "SolverList");
        ops_list.resize(params.size());
        for (int i=0; i<ops_list.size(); i++) {
            ops_list[i] = ParSolverT<_ValT, _GlobalIdxT, _LocalIdxT>::getFactory()->createInstance(params[i]);
        }
        return 0;
    }

    virtual void setup(const MatrixFree& freeA) {
        for (int i=0; i<ops_list.size(); i++) {
            ops_list[i]->setup(freeA);
        }
    }

    void solve(ParPreconditionerT<_ValT, _GlobalIdxT, _LocalIdxT> &P,
               ParMatrixFreeT<_ValT, _GlobalIdxT, _LocalIdxT> &A,
               const ParMatrixT<_ValT, _GlobalIdxT, _LocalIdxT> &b,
               ParMatrixT<_ValT, _GlobalIdxT, _LocalIdxT> &x, int &iter,
               double &relres) {
        auto norm_b = Vector::normL2(b);
        ScalarType norm_x0 = Vector::residual(A, x, b);
        ScalarType rel_res = norm_x0 / norm_b;
        int i;
        this->beginSolve(P, A, b, x, iter, relres);
        for (int i=0; i<ops_list.size(); i++) {
            ops_list[i]->solve(P, A, b, x, iter, relres);
            auto norm_res = Vector::residual(A, x, b);
            rel_res = norm_res / norm_b;
            this->logSolverStatus(P, i, norm_res, norm_res / norm_x0, rel_res);
            if (rel_res < rtol) {
                break;
            }
        }
        iter = i;
        relres = rel_res;
        this->finishSolve(P, max_its, iter, relres);
    }
};


template <class _ValT, class _GlobalIdxT, class _LocalIdxT>
class ParSmootherList_T: public ParSmootherT<_ValT, _GlobalIdxT, _LocalIdxT> {
public:
    

    using MatrixFree = ParMatrixFreeT<_ValT, _GlobalIdxT, _LocalIdxT>;
    using Vector = ParMatrixT<_ValT,  _GlobalIdxT, _LocalIdxT>;
    typedef typename TypeInfo<_ValT>::scalar_type ScalarType;


    std::vector<std::shared_ptr<ParSmootherT<_ValT, _GlobalIdxT, _LocalIdxT>>> ops_list;

    int create(const JsonValue& params) {
        ops_list.resize(params.size());
        for (int i=0; i<ops_list.size(); i++) {
            ops_list[i] = ParSmootherT<_ValT, _GlobalIdxT, _LocalIdxT>::getFactory()->createInstance(params[i]);
        }
        return 0;
    }

    virtual void setup(const MatrixFree& freeA) {
        for (int i=0; i<ops_list.size(); i++) {
            ops_list[i]->setup(freeA);
        }
    }
    virtual void smooth(const Vector& b, Vector& x) {
        for (int i=0; i<ops_list.size(); i++) {
            ops_list[i]->smooth(b, x);
        }
    }
};

template <class _ValT, class _GlobalIdxT, class _LocalIdxT>
class ParPrecondList_T: public ParPreconditionerT<_ValT, _GlobalIdxT, _LocalIdxT> {
public:
    

    using MatrixFree = ParMatrixFreeT<_ValT, _GlobalIdxT, _LocalIdxT>;
    using Vector = ParMatrixT<_ValT,  _GlobalIdxT, _LocalIdxT>;
    typedef typename TypeInfo<_ValT>::scalar_type ScalarType;


    std::vector<std::shared_ptr<ParPreconditionerT<_ValT, _GlobalIdxT, _LocalIdxT>>> ops_list;

    int create(const JsonValue& params) {
        ops_list.resize(params.size());
        for (int i=0; i<ops_list.size(); i++) {
            ops_list[i] = ParPreconditionerT<_ValT, _GlobalIdxT, _LocalIdxT>::getFactory()->createInstance(params[i]);
        }
        return 0;
    }

    virtual void setup(const MatrixFree& freeA) {
        for (int i=0; i<ops_list.size(); i++) {
            ops_list[i]->setup(freeA);
        }
    }
    virtual void precondition(const Vector& b, Vector& x) {
        for (int i=0; i<ops_list.size(); i++) {
            ops_list[i]->precondition(b, x);
        }
    }
};

}