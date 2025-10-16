#pragma once
#include "hipo/utils/json.hpp"
#include "hipo/mat/ParCSRMatrix.hpp"
#include "hipo/mat/ParMatrix.hpp"
#include "hipo/operators/ParOperator.hpp"




namespace hipo {

template <class _ValT, class _GlobalIdxT, class _LocalIdxT>
class ParPreconditionerAMG_T : 
    public ParPreconditionerT<_ValT, _GlobalIdxT, _LocalIdxT>,
    public ParSolverT<_ValT, _GlobalIdxT, _LocalIdxT> {

public:
    using Matrix = ParCSRMatrixT<_ValT, _GlobalIdxT, _LocalIdxT>;
    using Vector = ParMatrixT<_ValT,  _GlobalIdxT, _LocalIdxT>;
    using Smoother = ParSmootherT<_ValT, _GlobalIdxT, _LocalIdxT>;
    using Prolongationer = ParProlongationerT<_ValT, _GlobalIdxT, _LocalIdxT>;
    using Restrictioner = ParRestrictionerT<_ValT, _GlobalIdxT, _LocalIdxT>;
    using CoarseSolver = ParSolverT<_ValT, _GlobalIdxT, _LocalIdxT>;

    using LevelTransfer = ParLevelTransferT<_ValT, _GlobalIdxT, _LocalIdxT>;

    typedef typename TypeInfo<_ValT>::scalar_type ScalarType;

    void evalRAP(const Matrix& R, const Matrix& A, const Matrix& P, Matrix& RAP) {
        RAP = R.multiply(A).multiply(P);
        RAP.sortRows();
    }

    class AMGLevel : public ParOperator {
    public:
        Matrix A;
        Matrix P;
        Matrix R;

        Vector e;
        Vector r;
        Vector rback;
        Vector g;

        Vector rhs;
        Vector sol;
        Vector res;
        std::shared_ptr<Smoother> pre_smoother;
        std::shared_ptr<Smoother> post_smoother;

        std::shared_ptr<Smoother> coarse_pre_smoother;
        std::shared_ptr<Smoother> coarse_post_smoother;

        std::shared_ptr<CoarseSolver> coarse_solver;
        std::shared_ptr<Restrictioner> restrictioner;
        std::shared_ptr<Prolongationer> prolongationer;
        std::shared_ptr<LevelTransfer> level_transfer;

        void saveToStream(std::ostream &os) {
            os << "A is ";
            A.getLocalMatrix().toDense().saveToStream(os);
            os << "P is ";
            P.getLocalMatrix().toDense().saveToStream(os);
            os << "R is ";
            R.getLocalMatrix().toDense().saveToStream(os);
        }

        ScalarType presmooth_acc = 1;
        ScalarType correction_acc = 1;
        ScalarType postsmooth_acc = 1;
    };

    std::vector<std::shared_ptr<AMGLevel>> levels;

    int max_levels = 20;
    int min_coarse_size = 10;
    
    int verbose = 0;
    double rtol = 1e-8;
    int max_its = 5000;
    int cycle_count = 0;

    ParCSRMatrixT<_ValT, _GlobalIdxT, _LocalIdxT> m_A;

    JsonValue params;
public:
    int create(const JsonValue &params) {
        this->params = params;
        ParSolverT<_ValT, _GlobalIdxT, _LocalIdxT>::create(params, "AMG");
        FACTORY_GET_JSON_VAL(max_levels, "max_levels", int);
        FACTORY_GET_JSON_VAL(min_coarse_size, "min_coarse_size", int);
        FACTORY_GET_JSON_VAL(verbose, "verbose", int);
        return 0;
    }

    void createCoarsestLevel(std::shared_ptr<AMGLevel>& level_op, const JsonValue& params);
    void setup(const ParMatrixFreeT<_ValT, _GlobalIdxT, _LocalIdxT>& A);

    void solve(ParPreconditionerT<_ValT, _GlobalIdxT, _LocalIdxT> &P,
               ParMatrixFreeT<_ValT, _GlobalIdxT, _LocalIdxT> &A,
               const ParMatrixT<_ValT, _GlobalIdxT, _LocalIdxT> &b,
               ParMatrixT<_ValT, _GlobalIdxT, _LocalIdxT> &x, int &iter,
               double &relres);
   
    void precondition(const ParMatrixT<_ValT, _GlobalIdxT, _LocalIdxT> &x, ParMatrixT<_ValT, _GlobalIdxT, _LocalIdxT> &y);

    void vcycle_recursive(int i, const ParMatrixT<_ValT, _GlobalIdxT, _LocalIdxT> &b, ParMatrixT<_ValT, _GlobalIdxT, _LocalIdxT> &x);

    void vcycle(const ParMatrixT<_ValT, _GlobalIdxT, _LocalIdxT> &b, ParMatrixT<_ValT, _GlobalIdxT, _LocalIdxT> &x);


    void amg_step(const ParMatrixT<_ValT, _GlobalIdxT, _LocalIdxT> &b, ParMatrixT<_ValT, _GlobalIdxT, _LocalIdxT> &x);
};


} // namespace hipo
