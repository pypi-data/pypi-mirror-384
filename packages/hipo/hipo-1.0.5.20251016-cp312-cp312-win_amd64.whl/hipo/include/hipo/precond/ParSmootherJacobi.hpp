#pragma once
#include "hipo/operators/ParOperator.hpp"
#include "hipo/mat/ParCSRMatrix.hpp"


namespace hipo {

template <class _ValT, class _GlobalIdxT, class _LocalIdxT>
class ParSmootherJacobi_T: public ParOpBaseT<_ValT, _GlobalIdxT, _LocalIdxT> {
public:
    double relax = 1;
    int nsweeps = 1;
    bool initial_zero = true;
    int iter = 0;
    int max_iters = 0;

    using ParSolverT<_ValT, _GlobalIdxT, _LocalIdxT>::rtol;
    using ParSolverT<_ValT, _GlobalIdxT, _LocalIdxT>::max_its;
    using ParSolverT<_ValT, _GlobalIdxT, _LocalIdxT>::verbose;
    using Matrix = ParCSRMatrixT<_ValT, _GlobalIdxT, _LocalIdxT>;
    using Vector = ParMatrixT<_ValT,  _GlobalIdxT, _LocalIdxT>;
    typedef typename TypeInfo<_ValT>::scalar_type ScalarType;

    Matrix A;
    Vector diag_recp;
    ScalarType res = 0;

    int create(const JsonValue& params) {
        FACTORY_GET_JSON_VAL(relax, "relax", double);
        FACTORY_GET_JSON_VAL(nsweeps, "nsweeps", int);
        FACTORY_GET_JSON_VAL(initial_zero, "initial_zero", bool);
        FACTORY_GET_JSON_VAL(max_iters, "max_iters", int);
        return 0;
    }

    virtual void setup(const ParMatrixFreeT<_ValT, _GlobalIdxT, _LocalIdxT>& freeA) {
        auto upval = dynamic_cast<const Matrix*>(&freeA);
        if (upval != 0) {
            this->A = *upval;
            diag_recp = A.getDiag();
            Vector::reciprocal(1, diag_recp);
        } else {
            LOG(FATAL) << "ParSOR setup should be a ParCSRMatrix!";
        }
    }

    void jacobi_step(const Vector& b, Vector& x, double relax) {
        Vector r;
        res = Vector::residual(A, x, b, r);
        Vector::axypbz(relax, diag_recp, r, 1, x);
    }

    virtual void smooth(const Vector& b, Vector& x) {

        for (int i = 0; i < nsweeps; i++) {
            jacobi_step(b, x, relax);
            if (verbose) {
                LOG(INFO) << "smooth " << i << " " << Vector::residual(A, x, b);
            }
        }
    }

    virtual void precondition(const Vector& b, Vector& x) {

        if (initial_zero) {
            x.fill(0);
        }
        if (max_iters > 0 && iter >= max_iters) {
            b.deepCopy(x);
            return;
        }
        for (int i = 0; i < nsweeps; i++) {
            iter++;
            jacobi_step(b, x, relax);
            if (verbose) {
                LOG(INFO) << "precondition " << i << " " << Vector::residual(A, x, b);
            }
        }
    }

    void solve(ParPreconditionerT<_ValT, _GlobalIdxT, _LocalIdxT> &P_,
               ParMatrixFreeT<_ValT, _GlobalIdxT, _LocalIdxT> &A_,
               const ParMatrixT<_ValT, _GlobalIdxT, _LocalIdxT> &b,
               ParMatrixT<_ValT, _GlobalIdxT, _LocalIdxT> &x, int &iter,
               double &relres) {
        auto resb = Vector::normL2(b);
        ScalarType rel_res = Vector::residual(A, x, b) / resb;
        int i;
        for (i = 1; i <= max_its; i++) {
            jacobi_step(b, x, relax);
            rel_res = Vector::residual(A, x, b) / resb;
            if (verbose) {
                LOG(INFO) << "solve " << i << " " << rel_res;
            }
            if (rel_res < rtol) {
                break;
            }
        }
        iter = i;
        relres = rel_res;
    }
};



template <class _ValT, class _GlobalIdxT, class _LocalIdxT>
class ParSmootherJacobiLp_T: public ParSmootherJacobi_T<_ValT, _GlobalIdxT, _LocalIdxT> {
public:
    using Matrix = ParCSRMatrixT<_ValT, _GlobalIdxT, _LocalIdxT>;
    using Vector = ParMatrixT<_ValT,  _GlobalIdxT, _LocalIdxT>;
    double order = 2;
    int create(const JsonValue& params) {
        ParSmootherJacobi_T<_ValT, _GlobalIdxT, _LocalIdxT>::create(params);
        FACTORY_GET_JSON_VAL(order, "order", double);
        return 0;
    }
    virtual void setup(const ParMatrixFreeT<_ValT, _GlobalIdxT, _LocalIdxT>& freeA) {
        auto upval = dynamic_cast<const Matrix*>(&freeA);
        if (upval != 0) {
            this->A = *upval;
            auto diag = this->A.getDiag();
            auto rowNorm = this->A.rowNorm(this->order);
            Vector rowNormVal;
            rowNormVal.createComplex(rowNorm, decltype(rowNorm)());
            Vector::pow(this->order, rowNormVal);
            Vector::reciprocal(1, rowNormVal);
            this->diag_recp.create(diag.getRowPartitioner(), diag.getDevice(), diag.getComm());
            this->diag_recp.fill(0);
            Vector::axypbz(1, diag, rowNormVal, 0, this->diag_recp);
        } else {
            LOG(FATAL) << "ParSOR setup should be a ParCSRMatrix!";
        }
    }
};

}
