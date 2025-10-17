#pragma once
#include "hipo/operators/ParOperator.hpp"
#include "hipo/mat/ParCSRMatrix.hpp"
#include "hipo/ops/SpBlasOps.hpp"


namespace hipo {

template <class _ValT, class _GlobalIdxT, class _LocalIdxT>
class ParSmootherSOR_T: public ParOpBaseT<_ValT, _GlobalIdxT, _LocalIdxT> {
public:
    double relax = 1;
    bool forward = true;
    int nsweeps = 1;
    bool initial_zero = true;
    // compute x = S(A,b,x)

    using ParSolverT<_ValT, _GlobalIdxT, _LocalIdxT>::verbose;
    using ParSolverT<_ValT, _GlobalIdxT, _LocalIdxT>::max_its;
    using ParSolverT<_ValT, _GlobalIdxT, _LocalIdxT>::rtol;

    using Matrix = ParCSRMatrixT<_ValT, _GlobalIdxT, _LocalIdxT>;
    using Vector = ParMatrixT<_ValT,  _GlobalIdxT, _LocalIdxT>;
    typedef typename TypeInfo<_ValT>::scalar_type ScalarType;

    Matrix A;

    Vector diag;

    int myrank;

    MatrixT<COT_SpMVCSRRawMat<_ValT, _LocalIdxT>, _LocalIdxT> A_col_blk_raw, A_col_blk_raw_host;

    int create(const JsonValue& params) {
        ParSolverT<_ValT, _GlobalIdxT, _LocalIdxT>::create(params, "SOR");
        FACTORY_GET_JSON_VAL(relax, "relax", double);
        FACTORY_GET_JSON_VAL(forward, "forward", bool);
        FACTORY_GET_JSON_VAL(nsweeps, "nsweeps", int);
        FACTORY_GET_JSON_VAL(initial_zero, "initial_zero", int);
        return 0;
    }

    virtual void setup(const ParMatrixFreeT<_ValT, _GlobalIdxT, _LocalIdxT>& freeA) {
        auto upval = dynamic_cast<const Matrix*>(&freeA);
        if (upval != 0) {
            this->A = *upval;
            diag = this->A.getDiag();
            MPI_Comm_rank(this->A.getComm(), &myrank);      
        } else {
            LOG(FATAL) << "ParSOR setup should be a ParCSRMatrix!";
        }
    }

    virtual void sor_step(const Vector& b, Vector& x, double relax, bool forward, _LocalIdxT* sweep_ordering = 0) {
        auto lA = A.getLocalMatrix();
        auto lb = b.getLocalMatrix();
        auto lx = x.getLocalMatrix();
        auto ldiag = diag.getLocalMatrix();
        A.exchangeMatVec(x);
        this->A.getRawMat(A_col_blk_raw_host);
        A_col_blk_raw_host.toDevice(this->A.getDevice(), A_col_blk_raw);
        SpBlasOps<_ValT, _LocalIdxT>::par_sor(lA.getDevice(), lA.getRows(), myrank, A_col_blk_raw.getSize(), A_col_blk_raw.getData(),
        lb.getData(),
        ldiag.getData(),
        lx.getData(),
        relax, forward, sweep_ordering);
    }


    virtual void smooth(const Vector& b, Vector& x) {

        for (int i = 0; i < nsweeps; i++) {
            sor_step(b, x, relax, forward);
            if (verbose) {
                LOG(INFO) << "smooth " << i << " " << Vector::residual(A, x, b);
            }
        }
    }

    virtual void precondition(const Vector& b, Vector& x) {
        if (initial_zero) {
            x.fill(0);
        }
        for (int i = 0; i < nsweeps; i++) {
            sor_step(b, x, relax, forward);
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
        ScalarType norm_b = Vector::normL2(b);
        ScalarType norm_x0 = Vector::residual(A, x, b);
        ScalarType rel_res = norm_x0 / norm_b;
        int i;
        this->beginSolve(P_, A_, b, x, iter, relres);
        for (i = 1; i <= max_its; i++) {
            sor_step(b, x, relax, forward);
            auto res = Vector::residual(A, x, b);
            rel_res = res / norm_b;
            this->logSolverStatus(P_, i, res, res / norm_x0, rel_res);
            if (rel_res < rtol) {
                break;
            }
        }
        iter = i;
        relres = rel_res;
        this->finishSolve(P_, max_its, iter, relres);
    }
};



template <class _ValT, class _GlobalIdxT, class _LocalIdxT>
class ParSmootherSSOR_T: public ParSmootherSOR_T<_ValT, _GlobalIdxT, _LocalIdxT> {
public:
    using Vector = ParMatrixT<_ValT,  _GlobalIdxT, _LocalIdxT>;
    virtual void sor_step(const Vector& b, Vector& x, double relax, bool forward, _LocalIdxT* sweep_ordering = 0) {
        ParSmootherSOR_T<_ValT, _GlobalIdxT, _LocalIdxT>::sor_step(b, x, relax, forward, sweep_ordering);
        ParSmootherSOR_T<_ValT, _GlobalIdxT, _LocalIdxT>::sor_step(b, x, relax, !forward, sweep_ordering);
    }

};

}
