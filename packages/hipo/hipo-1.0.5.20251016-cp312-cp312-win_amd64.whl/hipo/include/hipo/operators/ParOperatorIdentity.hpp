#pragma once

#include "ParOperator.hpp"
#include "hipo/mat/ParCSRMatrix.hpp"

namespace hipo {

template <class _ValT, class _GlobalIdxT, class _LocalIdxT>
class ParOperatorIdentityT : public ParMatrixFreeT<_ValT, _GlobalIdxT, _LocalIdxT>,
                             public ParPreconditionerT<_ValT, _GlobalIdxT, _LocalIdxT>,
                             public ParSolverT<_ValT, _GlobalIdxT, _LocalIdxT>,
                             public ParSmootherT<_ValT, _GlobalIdxT, _LocalIdxT> {
public:
    using Vector = ParVectorT<_ValT, _GlobalIdxT, _LocalIdxT>;
    using MatrixFree = ParMatrixFreeT<_ValT, _GlobalIdxT, _LocalIdxT>;

    void create(const JsonValue& params) {}

    virtual MPI_Comm getComm() const { return MPI_COMM_WORLD; };
    virtual Device getDevice() const { return Device(Device::CPU); };
    virtual _GlobalIdxT getRows() const { return 0; }
    virtual _GlobalIdxT getCols() const { return 0; }
    virtual void aAxpby(_ValT a, const ParMatrixT<_ValT, _GlobalIdxT, _LocalIdxT>& x, _ValT b, 
    ParMatrixT<_ValT, _GlobalIdxT, _LocalIdxT>& y, typename MatrixFree::AsyncMatVecObject* asyncObj) { x.deepCopy(y); }
    virtual void setup(const MatrixFree &A) {}
    virtual void precondition(const Vector &x, Vector &y) { x.deepCopy(y); }
    void solve(ParPreconditionerT<_ValT, _GlobalIdxT, _LocalIdxT> &P,
               ParMatrixFreeT<_ValT, _GlobalIdxT, _LocalIdxT> &A,
               const ParMatrixT<_ValT, _GlobalIdxT, _LocalIdxT> &b,
               ParMatrixT<_ValT, _GlobalIdxT, _LocalIdxT> &x, int &iter,
               double &relres) {
        P.precondition(b, x);
    }
    virtual void smooth(const Vector& b, Vector& x) {
        // x_{n+1} = x_{n}
    }
};


} // namespace hipo
