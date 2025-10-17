#pragma once
#include "hipo/mat/Matrix_fwd.hpp"
#include "hipo/operators/ParOperator_fwd.hpp"
#include "hipo/utils/Device.hpp"
#include "hipo/utils/Factory.hpp"
#include "hipo/utils/json.hpp"
#include <future>
#include <string>
#include <list>
#include "hipo/comm/smpi.hpp"
#include "ParOperatorBase.hpp"
#include "hipo/utils/TickMeter.hpp"

namespace hipo {

#define FACTORY_GET_JSON_VAL(to, from, type)                                                                                               \
    if (params.contains(from)) {                                                                                                           \
        to = decltype(to)(params[from].get<type>());                                                                                       \
    }


template <class _ValT, class _GlobalIdxT, class _LocalIdxT=_GlobalIdxT>
class HIPO_WIN_API ParMatrixFreeT : public virtual ParOperator {
public:
    static Factory<ParMatrixFreeT> *getFactory();
    using Vector = ParVectorT<_ValT, _GlobalIdxT, _LocalIdxT>;
    using MatrixFree = ParMatrixFreeT<_ValT, _GlobalIdxT, _LocalIdxT>;
    virtual MPI_Comm getComm() const = 0;
    virtual Device getDevice() const = 0;
    virtual _GlobalIdxT getRows() const = 0;
    virtual _GlobalIdxT getCols() const = 0;
    class AsyncMatVecObject {
    public:
        std::promise<int> promise;
        int wait() {
            return promise.get_future().get();
        }
    };
    virtual void aAxpby(_ValT a, const ParMatrixT<_ValT, _GlobalIdxT, _LocalIdxT>& x, _ValT b, ParMatrixT<_ValT, _GlobalIdxT, _LocalIdxT>& y, AsyncMatVecObject* asyncObj=0) = 0;
    virtual void matVec(const Vector &x, Vector &y, AsyncMatVecObject* async = 0) {
        aAxpby(_ValT(1), x, _ValT(0), y, async);
    }
};

template <class _ValT, class _GlobalIdxT, class _LocalIdxT=_GlobalIdxT>
class HIPO_WIN_API ParPreconditionerT : public virtual ParOperator {
public:
    static Factory<ParPreconditionerT> *getFactory();
    using Vector = ParVectorT<_ValT, _GlobalIdxT, _LocalIdxT>;
    using MatrixFree = ParMatrixFreeT<_ValT, _GlobalIdxT, _LocalIdxT>;
    virtual void setup(const MatrixFree &A) = 0;
    virtual void precondition(const Vector &x, Vector &y) = 0;
    TickMeter setup_time;
    TickMeter precond_time;
};

template <class _ValT, class _GlobalIdxT, class _LocalIdxT=_GlobalIdxT>
class HIPO_WIN_API ParSolverT : public virtual ParOperator {
public:
    static Factory<ParSolverT> *getFactory();
    using Vector = ParVectorT<_ValT, _GlobalIdxT, _LocalIdxT>;
    using MatrixFree = ParMatrixFreeT<_ValT, _GlobalIdxT, _LocalIdxT>;
    using Precond = ParPreconditionerT<_ValT, _GlobalIdxT, _LocalIdxT>;
    
    typedef typename TypeInfo<_ValT>::scalar_type ScalarType;

    std::shared_ptr<Precond> m_precond;
    virtual void setup(const MatrixFree &A) = 0;
    virtual void solve(Precond &P, MatrixFree &A, const Vector &b, Vector &x, int &iter, double &relres) = 0;
    virtual void solve(MatrixFree &A, const Vector &b, Vector &x, int &iter, double &relres) {
        this->solve(*m_precond, A, b, x, iter, relres);
    }

protected:
    int nprocs, myrank;
    std::string name;
    int verbose = 0;
    double rtol = 1e-8;
    int max_its = 2000;
    double last_res = 1;
    hipo::TickMeter solve_time;
public:
    int create(const JsonValue& params, const std::string& name, bool need_precond = false) {
        if (need_precond) {
            JsonValue precond_params;
            if (params.contains("preconditioner")) {
                precond_params = params["preconditioner"];
            } else {
                precond_params["preconditioner_type"] = "PrecondIdentity";
            }
            m_precond = ParPreconditionerT<_ValT, _GlobalIdxT, _LocalIdxT>::getFactory()->createInstance(precond_params, this);
            this->appendChild(m_precond, "preconditioner");
        }

        FACTORY_GET_JSON_VAL(verbose, "verbose", int);
        FACTORY_GET_JSON_VAL(rtol, "rtol", double);
        FACTORY_GET_JSON_VAL(max_its, "max_its", int);
        this->name = name;
        return 0;
    }
    void beginSolve(Precond &P, MatrixFree &A, const Vector &b, Vector &x, int &iter, double &relres);
    void logSolverStatus(Precond &P, int iters, ScalarType res, ScalarType res_r0, ScalarType res_b);
    void finishSolve(Precond &P, int max_its, int iters, double relres);
};


template <class _ValT, class _GlobalIdxT, class _LocalIdxT=_GlobalIdxT>
class HIPO_WIN_API ParEigenSolverT : public virtual ParOperator {
public:
    static Factory<ParEigenSolverT> *getFactory();
    using Vector = ParVectorT<_ValT, _GlobalIdxT, _LocalIdxT>;
    using MatrixFree = ParMatrixFreeT<_ValT, _GlobalIdxT, _LocalIdxT>;
    using Precond = ParPreconditionerT<_ValT, _GlobalIdxT, _LocalIdxT>;
    
    typedef typename TypeInfo<_ValT>::scalar_type ScalarType;

    std::shared_ptr<Precond> m_precond;
    virtual void setup(const MatrixFree &A) = 0;
    virtual void solve(Precond &P, MatrixFree &A, MatrixFree &B, const Vector &y, Vector &x, Vector &lambda, int &iter, Vector &res) = 0;
};

template <class _ValT, class _GlobalIdxT, class _LocalIdxT=_GlobalIdxT>
class HIPO_WIN_API ParSmootherT : public virtual ParOperator {
public:
    static Factory<ParSmootherT> *getFactory();
    using Vector = ParVectorT<_ValT, _GlobalIdxT, _LocalIdxT>;
    using MatrixFree = ParMatrixFreeT<_ValT, _GlobalIdxT, _LocalIdxT>;
    virtual void setup(const MatrixFree &A) = 0;
    virtual void smooth(const Vector &b, Vector &x) = 0;
};

template <class _ValT, class _GlobalIdxT, class _LocalIdxT=_GlobalIdxT>
class HIPO_WIN_API ParOpBaseT : public ParSmootherT<_ValT, _GlobalIdxT, _LocalIdxT>,
                   public ParPreconditionerT<_ValT, _GlobalIdxT, _LocalIdxT>,
                   public ParSolverT<_ValT, _GlobalIdxT, _LocalIdxT> {
public:
    using ParSolverT<_ValT, _GlobalIdxT, _LocalIdxT>::setup;
    static Factory<ParOpBaseT> *getFactory();


};

template <class _ValT, class _GlobalIdxT, class _LocalIdxT=_GlobalIdxT>
class HIPO_WIN_API ParRestrictionerT : public ParOperator {
public:
    static Factory<ParRestrictionerT> *getFactory();
    using Vector = ParVectorT<_ValT, _GlobalIdxT, _LocalIdxT>;
    using MatrixFree = ParMatrixFreeT<_ValT, _GlobalIdxT, _LocalIdxT>;
    virtual void setup(const MatrixFree &A) = 0;
    virtual void restriction(const Vector &x, Vector &y) const = 0;
};

template <class _ValT, class _GlobalIdxT, class _LocalIdxT=_GlobalIdxT>
class HIPO_WIN_API ParProlongationerT : public ParOperator {
public:
    static Factory<ParProlongationerT> *getFactory();
    using Vector = ParVectorT<_ValT, _GlobalIdxT, _LocalIdxT>;
    using MatrixFree = ParMatrixFreeT<_ValT, _GlobalIdxT, _LocalIdxT>;
    virtual void setup(const MatrixFree &A) = 0;
    virtual void prolongation(const Vector &x, Vector &y) = 0;
};

template <class _ValT, class _GlobalIdxT, class _LocalIdxT=_GlobalIdxT>
class HIPO_WIN_API ParLevelTransferT : public virtual ParOperator {
public:
    static Factory<ParLevelTransferT> *getFactory();
    using Vector = ParVectorT<_ValT, _GlobalIdxT, _LocalIdxT>;
    using MatrixFree = ParMatrixFreeT<_ValT, _GlobalIdxT, _LocalIdxT>;
    using Matrix = ParCSRMatrixT<_ValT, _GlobalIdxT, _LocalIdxT>;
    virtual void transfer_operators(const Matrix &A, Matrix &P, Matrix &R) = 0;
    void setLevelId(int id);
    int getLevelId() const;
    ParLevelTransferT();

    struct ParLevelTransferImpl {
        ParCSRMatrixT<_ValT, _GlobalIdxT,_LocalIdxT> A;
        ParMatrixT<_ValT, _GlobalIdxT, _LocalIdxT> diag;
        ParCSRMatrixT<_LocalIdxT,_GlobalIdxT, _LocalIdxT> S;
        ParMatrixT<_LocalIdxT, _GlobalIdxT, _LocalIdxT> cf;
        _GlobalIdxT naggr = 0;
        ParMatrixT<_LocalIdxT, _GlobalIdxT, _LocalIdxT> aggr;
        ParCSRMatrixT<_ValT, _GlobalIdxT, _LocalIdxT> P_tent;
        ParCSRMatrixT<_ValT, _GlobalIdxT, _LocalIdxT> P;
        ParCSRMatrixT<_ValT, _GlobalIdxT, _LocalIdxT> R;
        ParCSRMatrixT<_ValT, _GlobalIdxT, _LocalIdxT> RAP;
        int level_id = 0;
    };
    std::shared_ptr<ParLevelTransferImpl> getData() {
        return m_impl;
    }
protected:
    std::shared_ptr<ParLevelTransferImpl> m_impl;
};

#define LEVEL_TRANSFER_MEMBER \
public:\
    ParLevelTransferT<_ValT, _GlobalIdxT, _LocalIdxT>* getLevelTransfer() {\
        return level_transfer_;\
    }\
    void setLevelTransfer(ParLevelTransferT<_ValT, _GlobalIdxT, _LocalIdxT>* lt) {\
        level_transfer_ = lt;\
    }\
protected:\
    ParLevelTransferT<_ValT, _GlobalIdxT, _LocalIdxT>* level_transfer_ = 0;


template <class _ValT, class _GlobalIdxT, class _LocalIdxT=_GlobalIdxT>
class HIPO_WIN_API ParStrengtherT : public virtual ParOperator {
public:
    static Factory<ParStrengtherT> *getFactory();
    using Vector = ParVectorT<_ValT, _GlobalIdxT, _LocalIdxT>;
    using MatrixFree = ParMatrixFreeT<_ValT, _GlobalIdxT, _LocalIdxT>;
    using Matrix = ParCSRMatrixT<_ValT, _GlobalIdxT, _LocalIdxT>;
    virtual void strength(const Matrix &A, const Vector& diag, ParCSRMatrixT<_LocalIdxT, _GlobalIdxT, _LocalIdxT> &S) = 0;

    LEVEL_TRANSFER_MEMBER
};



template <class _ValT, class _GlobalIdxT, class _LocalIdxT=_GlobalIdxT>
class HIPO_WIN_API ParAggregatorT : public virtual ParOperator {
public:
    static Factory<ParAggregatorT> *getFactory();
    using Vector = ParVectorT<_ValT, _GlobalIdxT, _LocalIdxT>;
    using MatrixFree = ParMatrixFreeT<_ValT, _GlobalIdxT, _LocalIdxT>;
    using Matrix = ParCSRMatrixT<_ValT, _GlobalIdxT, _LocalIdxT>;
    virtual void aggregate(const Matrix &A, const ParCSRMatrixT<_LocalIdxT, _GlobalIdxT, _LocalIdxT> &S, ParVectorT<_LocalIdxT, _GlobalIdxT, _LocalIdxT> &aggr, _GlobalIdxT& naggr) = 0;

    LEVEL_TRANSFER_MEMBER
};

template <class _ValT, class _GlobalIdxT, class _LocalIdxT=_GlobalIdxT>
class HIPO_WIN_API ParSplitterT : public virtual ParOperator {
public:
    static Factory<ParSplitterT> *getFactory();
    using Vector = ParVectorT<_ValT, _GlobalIdxT, _LocalIdxT>;
    using MatrixFree = ParMatrixFreeT<_ValT, _GlobalIdxT, _LocalIdxT>;
    using Matrix = ParCSRMatrixT<_ValT, _GlobalIdxT, _LocalIdxT>;
    virtual void split(const Matrix &A, ParCSRMatrixT<_LocalIdxT, _GlobalIdxT, _LocalIdxT> &S, ParVectorT<_LocalIdxT, _GlobalIdxT, _LocalIdxT> &cfsplit) = 0;

    LEVEL_TRANSFER_MEMBER
};

template <class _ValT, class _GlobalIdxT, class _LocalIdxT=_GlobalIdxT>
class HIPO_WIN_API ParInterpolatorT : public virtual ParOperator {
public:
    static Factory<ParInterpolatorT> *getFactory();
    using Vector = ParVectorT<_ValT, _GlobalIdxT, _LocalIdxT>;
    using MatrixFree = ParMatrixFreeT<_ValT, _GlobalIdxT, _LocalIdxT>;
    using Matrix = ParCSRMatrixT<_ValT, _GlobalIdxT, _LocalIdxT>;
    virtual void interpolate(const Matrix &A,  const ParCSRMatrixT<_LocalIdxT, _GlobalIdxT, _LocalIdxT> &S, const ParVectorT<_LocalIdxT, _GlobalIdxT, _LocalIdxT> &cfsplit, _GlobalIdxT& naggr, ParVectorT<_LocalIdxT, _GlobalIdxT, _LocalIdxT> &aggr, Matrix &P) = 0;

    LEVEL_TRANSFER_MEMBER
};


template <class _ValT, class _GlobalIdxT, class _LocalIdxT=_GlobalIdxT>
class HIPO_WIN_API ParAggrInterpolatorT : public virtual ParOperator {
public:
    static Factory<ParAggrInterpolatorT> *getFactory();
    using Vector = ParVectorT<_ValT, _GlobalIdxT, _LocalIdxT>;
    using MatrixFree = ParMatrixFreeT<_ValT, _GlobalIdxT, _LocalIdxT>;
    using Matrix = ParCSRMatrixT<_ValT, _GlobalIdxT, _LocalIdxT>;
    virtual void interpolate(const Matrix &A,  const ParCSRMatrixT<_LocalIdxT, _GlobalIdxT, _LocalIdxT> &S, const _GlobalIdxT& naggr, const ParVectorT<_LocalIdxT, _GlobalIdxT, _LocalIdxT> &aggr, Matrix& P_tent, Matrix &P) = 0;

    LEVEL_TRANSFER_MEMBER
};

template <class _ValT, class _GlobalIdxT, class _LocalIdxT=_GlobalIdxT>
class HIPO_WIN_API OperatorGallery {
public:
    static std::string getAllInstances(std::map<std::string, std::vector<std::string>>* maps = 0) { 
        std::ostringstream oss;

        oss << "Solver" << std::endl;
        for (auto& item : *ParSolverT<_ValT, _GlobalIdxT, _LocalIdxT>::getFactory()->getCreatorMap()) {
            oss << "  " << item.first << std::endl;
            if (maps) {
                (*maps)["Solver"].push_back(item.first);
            }
        }
        oss << "Preconditioner" << std::endl;
        for (auto& item : *ParPreconditionerT<_ValT, _GlobalIdxT, _LocalIdxT>::getFactory()->getCreatorMap()) {
            oss << "  " << item.first << std::endl;
            if (maps) {
                (*maps)["Preconditioner"].push_back(item.first);
            }
        }
        oss << "Smoother" << std::endl;
        for (auto& item : *ParSmootherT<_ValT, _GlobalIdxT, _LocalIdxT>::getFactory()->getCreatorMap()) {
            oss << "  " << item.first << std::endl;
            if (maps) {
                (*maps)["Smoother"].push_back(item.first);
            }
        }
        oss << "LevelTransfer" << std::endl;
        for (auto& item : *ParLevelTransferT<_ValT, _GlobalIdxT, _LocalIdxT>::getFactory()->getCreatorMap()) {
            oss << "  " << item.first << std::endl;
            if (maps) {
                (*maps)["LevelTransfer"].push_back(item.first);
            }
        }
        oss << "Strengther" << std::endl;
        for (auto& item : *ParStrengtherT<_ValT, _GlobalIdxT, _LocalIdxT>::getFactory()->getCreatorMap()) {
            oss << "  " << item.first << std::endl;
            if (maps) {
                (*maps)["Strengther"].push_back(item.first);
            }
        }
        oss << "Splitter" << std::endl;
        for (auto& item : *ParSplitterT<_ValT, _GlobalIdxT, _LocalIdxT>::getFactory()->getCreatorMap()) {
            oss << "  " << item.first << std::endl;
            if (maps) {
                (*maps)["Splitter"].push_back(item.first);
            }
        }
        
        oss << "Interpolator" << std::endl;
        for (auto& item : *ParInterpolatorT<_ValT, _GlobalIdxT, _LocalIdxT>::getFactory()->getCreatorMap()) {
            oss << "  " << item.first << std::endl;
            if (maps) {
                (*maps)["Interpolator"].push_back(item.first);
            }
        }

        oss << "Aggregator" << std::endl;
        for (auto& item : *ParAggregatorT<_ValT, _GlobalIdxT, _LocalIdxT>::getFactory()->getCreatorMap()) {
            oss << "  " << item.first << std::endl;
            if (maps) {
                (*maps)["Aggregator"].push_back(item.first);
            }
        }

        oss << "AggrInterpolator" << std::endl;
        for (auto& item : *ParAggrInterpolatorT<_ValT, _GlobalIdxT, _LocalIdxT>::getFactory()->getCreatorMap()) {
            oss << "  " << item.first << std::endl;
            if (maps) {
                (*maps)["AggrInterpolator"].push_back(item.first);
            }
        }

        oss << "EigenSolver" << std::endl;
        for (auto& item : *ParEigenSolverT<_ValT, _GlobalIdxT, _LocalIdxT>::getFactory()->getCreatorMap()) {
            oss << "  " << item.first << std::endl;
            if (maps) {
                (*maps)["EigenSolver"].push_back(item.first);
            }
        }

        return oss.str();
    }
};

} // namespace hipo

#define FACTORY_REGISTER(name, BaseT, DeriveT, ValType, GlobalType, LocalType)                                                             \
    FactoryRegisterer<BaseT<ValType, GlobalType, LocalType>, DeriveT<ValType, GlobalType, LocalType>>                                      \
        __register__##BaseT##__##name##__##DeriveT##__##ValType##__##GlobalType##__##LocalType(#BaseT, #name)


#define FACTORY_REGISTER_MP(name, BaseT, DeriveT, NewValType, ValType, GlobalType, LocalType)                                                             \
    FactoryRegisterer<BaseT<ValType, GlobalType, LocalType>, DeriveT<NewValType, ValType, GlobalType, LocalType>>                                      \
        __register__##BaseT##__##name##__##DeriveT##__##NewValType##__##ValType##__##GlobalType##__##LocalType(#BaseT, #name)


