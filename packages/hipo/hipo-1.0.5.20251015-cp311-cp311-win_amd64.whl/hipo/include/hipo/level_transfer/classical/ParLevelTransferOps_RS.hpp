#pragma once
#include "hipo/operators/ParOperator.hpp"
#include "hipo/mat/ParCSRMatrix.hpp"

namespace hipo {


template <class _ValT, class _GlobalIdxT, class _LocalIdxT>
class HIPO_WIN_API LevelTransferOps_RS {
public:
    typedef typename TypeInfo<_ValT>::scalar_type ScalarT;
    static void connect(const CSRMatrixT<_ValT, _LocalIdxT>& A, ScalarT eps_strong,
     CSRMatrixT<_LocalIdxT, _LocalIdxT>& S,
     MatrixT<_LocalIdxT, _LocalIdxT>& cf
     );

    static void cfsplit(const CSRMatrixT<_ValT, _LocalIdxT>& A, const CSRMatrixT<_LocalIdxT, _LocalIdxT>& S, MatrixT<_LocalIdxT, _LocalIdxT>& cf);

    static void interpolation(const CSRMatrixT<_ValT, _LocalIdxT>& A, const CSRMatrixT<_LocalIdxT, _LocalIdxT>& S, 
    const MatrixT<_LocalIdxT, _LocalIdxT>& cf, bool do_trunc, ScalarT eps_trunc,
    _LocalIdxT coarse_tag, _LocalIdxT fine_tag,
    _LocalIdxT& num_aggr, CSRMatrixT<_ValT, _LocalIdxT>& P);


    static void par_connect(const ParCSRMatrixT<_ValT, _GlobalIdxT, _LocalIdxT>& A, ScalarT eps_strong,
        ParCSRMatrixT<_LocalIdxT, _GlobalIdxT,  _LocalIdxT>& S);

    static void par_BoomerAMGStrength(const ParCSRMatrixT<_ValT, _GlobalIdxT, _LocalIdxT>& A, 
        const ParMatrixT<_ValT, _GlobalIdxT, _LocalIdxT> &diag,
        ScalarT strong_threshold, 
        ScalarT max_row_sum, _LocalIdxT num_functions,
        ParCSRMatrixT<_LocalIdxT, _GlobalIdxT,  _LocalIdxT>& S);

    static void par_BoomerAMGCoarsenPMIS(
        const ParCSRMatrixT<_ValT, _GlobalIdxT, _LocalIdxT> &A, const ParCSRMatrixT<_LocalIdxT, _GlobalIdxT, _LocalIdxT> &S,
        ParMatrixT<_LocalIdxT, _GlobalIdxT, _LocalIdxT> &CF_Marker, _LocalIdxT CF_init
    );

    static void par_interpolation(const ParCSRMatrixT<_ValT,_GlobalIdxT, _LocalIdxT>& A, const ParCSRMatrixT<_LocalIdxT,_GlobalIdxT, _LocalIdxT>& S, 
        const ParMatrixT<_LocalIdxT,_GlobalIdxT, _LocalIdxT>& cf, bool do_trunc, ScalarT eps_trunc,
        _LocalIdxT coarse_tag, _LocalIdxT fine_tag,
        _GlobalIdxT& num_aggr, ParCSRMatrixT<_ValT,_GlobalIdxT, _LocalIdxT>& P);


    static void par_BoomerAMGInterpolationExtendedPI(
        const ParCSRMatrixT<_ValT, _GlobalIdxT, _LocalIdxT> &A, const ParCSRMatrixT<_LocalIdxT, _GlobalIdxT, _LocalIdxT> &S,
        const ParMatrixT<_LocalIdxT, _GlobalIdxT, _LocalIdxT> &cf, 
        _LocalIdxT num_functions, const MatrixT<_LocalIdxT, _LocalIdxT>& dof_func,
        ScalarT trunc_factor, _LocalIdxT p_max_elmts,
        _GlobalIdxT &num_aggr, ParMatrixT<_LocalIdxT, _GlobalIdxT, _LocalIdxT>& aggr,
        ParCSRMatrixT<_ValT, _GlobalIdxT, _LocalIdxT> &P);


    static void par_BoomerAMGCSRMatrixTruncate(
        const CSRMatrixT<_ValT, _LocalIdxT> &P,
        typename TypeInfo<_ValT>::scalar_type trunc_factor,
        _LocalIdxT           max_row_elmts,
        _LocalIdxT           rescale,
        _LocalIdxT           nrm_type,
        CSRMatrixT<_ValT, _LocalIdxT>& ret
    );
};

template <class _ValT, class _GlobalIdxT, class _LocalIdxT>
class HIPO_WIN_API SeqLevelTransferRugeStuben_T : public ParLevelTransferT<_ValT, _GlobalIdxT, _LocalIdxT> {
    using Matrix = ParCSRMatrixT<_ValT, _GlobalIdxT, _LocalIdxT>;
public:
    struct Impl {
        CSRMatrixT<_ValT, _LocalIdxT> A;
        CSRMatrixT<_LocalIdxT, _LocalIdxT> S;
        MatrixT<_LocalIdxT, _LocalIdxT> cf;
        _LocalIdxT naggr;
        CSRMatrixT<_ValT, _LocalIdxT> P;
        CSRMatrixT<_ValT, _LocalIdxT> RAP;
    };
    std::shared_ptr<Impl> m_impl;
    bool reserve = false;

    double eps_strong = 0.25;
    bool do_trunc = true;
    double eps_trunc = 0.2;
    _LocalIdxT coarse_tag = 'C';
    _LocalIdxT fine_tag = 'F';

    int create(const JsonValue &params) {
        FACTORY_GET_JSON_VAL(eps_strong, "eps_strong", double);
        FACTORY_GET_JSON_VAL(do_trunc, "do_trunc", bool);
        FACTORY_GET_JSON_VAL(eps_trunc, "eps_trunc", double);
        return 0;
    }
    virtual void transfer_operators(const Matrix& distA, Matrix& distP, Matrix& distR);
};


template <class _ValT, class _GlobalIdxT, class _LocalIdxT>
class HIPO_WIN_API ParLevelTransferRugeStuben_T : public SeqLevelTransferRugeStuben_T<_ValT, _GlobalIdxT, _LocalIdxT> {
    using Matrix = ParCSRMatrixT<_ValT, _GlobalIdxT, _LocalIdxT>;
public:
    struct Impl {
        ParCSRMatrixT<_ValT, _GlobalIdxT,_LocalIdxT> A;
        ParCSRMatrixT<_LocalIdxT,_GlobalIdxT, _LocalIdxT> S;
        ParMatrixT<_LocalIdxT, _GlobalIdxT, _LocalIdxT> cf;
        _GlobalIdxT naggr;
        ParCSRMatrixT<_ValT, _GlobalIdxT, _LocalIdxT> P;
        ParCSRMatrixT<_ValT, _GlobalIdxT, _LocalIdxT> RAP;
    };
    std::shared_ptr<Impl> m_impl;

    _LocalIdxT CF_init = 0;
    

    int create(const JsonValue &params) {
        SeqLevelTransferRugeStuben_T<_ValT, _GlobalIdxT,_LocalIdxT>::create(params);

        this->coarse_tag = 1;
        this->fine_tag = -1;

        return 0;
    }
    virtual void transfer_operators(const Matrix& distA, Matrix& distP, Matrix& distR);
};

} // namespace hipo
