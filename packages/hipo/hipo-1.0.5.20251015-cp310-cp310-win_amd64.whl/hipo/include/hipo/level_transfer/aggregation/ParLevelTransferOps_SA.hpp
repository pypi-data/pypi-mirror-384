#pragma once

#include "hipo/operators/ParOperator.hpp"
#include "hipo/mat/ParCSRMatrix.hpp"



namespace hipo {

template <class _ValT, class _GlobalIdxT, class _LocalIdxT>
class HIPO_WIN_API LevelTransferOps_SA {
public:
    // smooth aggregation functions
    static void seq_strength(const CSRMatrixT<_ValT, _LocalIdxT>& A, const MatrixT<_ValT, _LocalIdxT>& diag,  CSRMatrixT<_LocalIdxT, _LocalIdxT>& strength, typename TypeInfo<_ValT>::scalar_type eps_strong, _LocalIdxT normtype = 0);
    static void par_strength(const ParCSRMatrixT<_ValT, _GlobalIdxT, _LocalIdxT>& A, const ParMatrixT<_ValT, _GlobalIdxT, _LocalIdxT>& diag, ParCSRMatrixT<_LocalIdxT, _GlobalIdxT, _LocalIdxT>& strength, typename TypeInfo<_ValT>::scalar_type eps_strong, _LocalIdxT normtype = 0);


    static void seq_aggregate(const CSRMatrixT<_LocalIdxT, _LocalIdxT>& strength, _LocalIdxT max_aggregation, MatrixT<_LocalIdxT, _LocalIdxT>& cluster, _LocalIdxT& naggr);
    static void seq_aggregate(const ParCSRMatrixT<_LocalIdxT, _GlobalIdxT,  _LocalIdxT>& strength, _LocalIdxT max_aggregation, ParMatrixT<_LocalIdxT, _GlobalIdxT,  _LocalIdxT>& cluster, _GlobalIdxT& naggr);


    static void par_renumber(ParMatrixT<_LocalIdxT, _GlobalIdxT, _LocalIdxT> &cluster, ParMatrixT<_LocalIdxT, _GlobalIdxT, _LocalIdxT> &cluster_owner, _GlobalIdxT &naggr);
    static void par_aggregate(const ParCSRMatrixT<_LocalIdxT, _GlobalIdxT, _LocalIdxT>& strength, ParMatrixT<_LocalIdxT,  _GlobalIdxT, _LocalIdxT>& cluster, _GlobalIdxT& naggr);
    static void par_aggregate_comm_pattern(const ParCSRMatrixT<_LocalIdxT, _GlobalIdxT, _LocalIdxT>& strength, ParMatrixT<_LocalIdxT,  _GlobalIdxT, _LocalIdxT>& cluster, _GlobalIdxT& naggr);
    static void par_aggregate_ghost(const ParCSRMatrixT<_LocalIdxT, _GlobalIdxT, _LocalIdxT>& strength, ParMatrixT<_LocalIdxT,  _GlobalIdxT, _LocalIdxT>& cluster, _GlobalIdxT& naggr);

    // cluster和A具有相同的rowPartitioner
    static void seq_tentative_prolongation(_LocalIdxT naggr, const MatrixT<_LocalIdxT, _LocalIdxT>& cluster, CSRMatrixT<_ValT, _LocalIdxT>& P_tent);
    static void par_tentative_prolongation(_GlobalIdxT naggr, const ParMatrixT<_LocalIdxT, _GlobalIdxT, _LocalIdxT>& cluster, ParCSRMatrixT<_ValT, _GlobalIdxT, _LocalIdxT>& P_tent);


    static void seq_tentative_filter(const CSRMatrixT<_ValT, _LocalIdxT> &A, 
        const CSRMatrixT<_LocalIdxT, _LocalIdxT> &S,
        CSRMatrixT<_ValT, _LocalIdxT> &A_filter
    );

    static void par_tentative_filter(const ParCSRMatrixT<_ValT, _GlobalIdxT, _LocalIdxT> &A, 
        const ParCSRMatrixT<_LocalIdxT, _GlobalIdxT, _LocalIdxT> &strength,
        ParCSRMatrixT<_ValT, _GlobalIdxT, _LocalIdxT> &A_filter
    );

    static void seq_tentative_smooth(const CSRMatrixT<_ValT, _LocalIdxT> &A, _LocalIdxT naggr,
                                                                        const CSRMatrixT<_ValT, _LocalIdxT> &P_tent,
                                                                        const CSRMatrixT<_LocalIdxT, _LocalIdxT> &strength,
                                                                        CSRMatrixT<_ValT, _LocalIdxT> &P,
                                                                        typename TypeInfo<_ValT>::scalar_type omega);

    static void par_tentative_smooth(const ParCSRMatrixT<_ValT, _GlobalIdxT, _LocalIdxT> &A, _GlobalIdxT naggr,
                                                                        const ParCSRMatrixT<_ValT, _GlobalIdxT, _LocalIdxT> &P_tent,
                                                                        const ParCSRMatrixT<_LocalIdxT, _GlobalIdxT, _LocalIdxT> &strength,
                                                                        ParCSRMatrixT<_ValT, _GlobalIdxT, _LocalIdxT> &P,
                                                                        typename TypeInfo<_ValT>::scalar_type omega);
};


template <class _ValT, class _GlobalIdxT, class _LocalIdxT>
class HIPO_WIN_API SeqLevelTransferSmoothAggregation_T : public ParLevelTransferT<_ValT, _GlobalIdxT, _LocalIdxT> {
    using Matrix = ParCSRMatrixT<_ValT, _GlobalIdxT, _LocalIdxT>;
public:
    struct Impl {
        CSRMatrixT<_ValT, _LocalIdxT> A;
        MatrixT<_ValT, _LocalIdxT> diag;
        CSRMatrixT<_LocalIdxT, _LocalIdxT> S;
        MatrixT<_LocalIdxT, _LocalIdxT> cluster;
        _LocalIdxT naggr;
        CSRMatrixT<_ValT, _LocalIdxT> P_tent;
        CSRMatrixT<_ValT, _LocalIdxT> P;
        CSRMatrixT<_ValT, _LocalIdxT> RAP;
    };
    std::shared_ptr<Impl> m_impl;
    bool reserve = false;

    double eps_strong = 0.08;
    double relax = 1;
    int block_size = 1;
    bool smooth = true;
    bool verbose = false;
    std::shared_ptr<ParAggregatorT<_ValT, _GlobalIdxT, _LocalIdxT>> aggregator;
    JsonValue aggregator_json;
    std::string default_aggregator = "AggregatorVMBSeq";
    int create(const JsonValue &params) {
        FACTORY_GET_JSON_VAL(eps_strong, "eps_strong", double);
        FACTORY_GET_JSON_VAL(relax, "relax", double);
        FACTORY_GET_JSON_VAL(block_size, "block_size", int);
        FACTORY_GET_JSON_VAL(smooth, "smooth", bool);
        FACTORY_GET_JSON_VAL(aggregator_json, "aggregator", JsonValue);
        FACTORY_GET_JSON_VAL(verbose, "verbose", bool);

        if (!aggregator_json.contains("aggregator_type")) {
            aggregator_json["aggregator_type"] = default_aggregator;
        }
        aggregator = ParAggregatorT<_ValT, _GlobalIdxT, _LocalIdxT>::getFactory()->createInstance(aggregator_json);
        this->appendChild(aggregator, "aggregator");
        return 0;
    }
    virtual void transfer_operators(const Matrix& distA, Matrix& distP, Matrix& distR);
};


template <class _ValT, class _GlobalIdxT, class _LocalIdxT>
class HIPO_WIN_API ParLevelTransferSmoothAggregation_T : public SeqLevelTransferSmoothAggregation_T<_ValT, _GlobalIdxT, _LocalIdxT> {
    using Matrix = ParCSRMatrixT<_ValT, _GlobalIdxT, _LocalIdxT>;
public:
int create(const JsonValue &params) {
        this->default_aggregator = "AggregatorS2Greedy";
        SeqLevelTransferSmoothAggregation_T<_ValT, _GlobalIdxT, _LocalIdxT>::create(params);
        return 0;
    }
    virtual void transfer_operators(const Matrix& distA, Matrix& distP, Matrix& distR);
};


} // namespace hipo
