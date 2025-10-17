#pragma once

#include "hipo/operators/ParOperator.hpp"

namespace hipo {

template <class _ValT, class _GlobalIdxT, class _LocalIdxT, class _PValT = _ValT>
class EigenSolverLOBPCG_T : public ParEigenSolverT<_ValT, _GlobalIdxT, _LocalIdxT> {
public:

    using Vector = ParVectorT<_ValT, _GlobalIdxT, _LocalIdxT>;
    using MatrixFree = ParMatrixFreeT<_ValT, _GlobalIdxT, _LocalIdxT>;
    using Precond = ParPreconditionerT<_ValT, _GlobalIdxT, _LocalIdxT>;
    
    typedef typename TypeInfo<_ValT>::scalar_type ScalarType;

    int max_its;
    ScalarType rtol;
    ScalarType atol;
    EigenSolverLOBPCG_T();

    void setup(const ParMatrixFreeT<_ValT, _GlobalIdxT, _LocalIdxT> &A) {}

    int create(const JsonValue &params) {        
        return 0;
    }

    typedef ParMatrixT<_ValT, _GlobalIdxT, _LocalIdxT> MultiVector;
    typedef MatrixT<_ValT, _LocalIdxT> DenseMatrix;

    static void MultiVectorByMultiVector(const MultiVector& X, const MultiVector& Y, DenseMatrix& A);
    static void MultiVectorByMatrix(const MultiVector& X, const DenseMatrix& Y, MultiVector& Z);
    static void MultiVectorByMultiVectorDiag(const MultiVector& X, const MultiVector& Y, DenseMatrix& A);
    static void MultiVectorByDiagonal(const MultiVector& X, const DenseMatrix& diag, MultiVector& Y);

    static int solveGEVP(const DenseMatrix& A, const DenseMatrix& B, DenseMatrix& lambda);

    static int Cholesky(DenseMatrix& A);
    static void UpperInvAndClearL(DenseMatrix& A);
    static int MultiVectorImplicitQR(const MultiVector& x, const MultiVector& y, DenseMatrix& r, MultiVector* z = 0);
    


static int checkResiduals(const DenseMatrix &resNorms, const DenseMatrix &lambda, ScalarType rtol, ScalarType atol);


    void solve(Precond &P, MatrixFree &A, MatrixFree &B, const Vector &y, Vector &x, Vector &lambda, int &iter, Vector &res);
};


} // namespace hipo