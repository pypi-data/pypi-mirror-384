
#pragma once


#include "hipo/utils/Complex.hpp"
#include "hipo/utils/Device.hpp"



namespace hipo {
template <class _ValT, class _GlobalIdxT, class _IdxT>
class HIPO_WIN_API SpLevelTransferOps {
public:
    static void csr_strength(const Device& dev, COT_CSRRawMat<_ValT, _IdxT> A, const _ValT * diag, COT_CSRRawMat<_IdxT, _IdxT> S, typename TypeInfo<_ValT>::scalar_type eps, _IdxT type);
    static void par_csr_symmetric_strength(const Device& dev, _IdxT rows, _GlobalIdxT row_start, _IdxT myrank, _IdxT nblks, const COT_SpMVCSRRawMat<_ValT, _IdxT> * A_blks, const _ValT * diag, COT_RawCommPattern<_ValT, _IdxT> * ext_diag, typename TypeInfo<_ValT>::scalar_type strong_threshold, int type, COT_SpMVCSRRawMat<_IdxT, _IdxT> * S_blks);
    static void csr_aggregate(const Device& dev, COT_CSRRawMat<_IdxT, _IdxT> S, _IdxT max_aggregation, _IdxT * cluster, _IdxT * nclusters, _IdxT * work_cnt, _IdxT * work_neib);
    static void par_csr_aggregate(const Device& dev, AggregateStep step, _IdxT rows, _IdxT myrank, _IdxT nblks_S, COT_SpMVCSRRawMat<_IdxT, _IdxT> * S, _IdxT nblks_SS, COT_SpMVCSRRawMat<_IdxT, _IdxT> * SS, _IdxT * cluster, _IdxT * n_undone, _IdxT * cluster_owner, _IdxT * nclusters, AggregateData<_IdxT> * send_data, _IdxT * send_len, _IdxT * work_neib);
    static void par_csr_aggregate_comm_pattern(const Device& dev, AggregateStep step, _IdxT rows, _IdxT myrank, _IdxT nblks_S, COT_SpMVCSRRawMat<_IdxT, _IdxT> * S, _IdxT nblks_SS, COT_SpMVCSRRawMat<_IdxT, _IdxT> * SS, _IdxT * cluster, _IdxT cluster_exter_size, COT_RawCommPattern<_IdxT, _IdxT> * cluster_exter, _IdxT * n_undone, _IdxT * cluster_owner, _IdxT * nclusters, _IdxT * work_neib);
    static void par_csr_aggregate_ghost(const Device& dev, AggregateStep step, _IdxT rows, _IdxT rows_gw1, _IdxT row_start, _IdxT nprocs, _IdxT myrank, _IdxT nblks_S, COT_SpMVCSRRawMat<_IdxT, _IdxT> * S, const _IdxT * S_global_to_local, _IdxT * loc_state, COT_RawCommPattern<_IdxT, _IdxT> * ext_state, _IdxT * pn_aggr, _IdxT * pn_undone, _IdxT serial_mode, _IdxT * work_neib);
    static void par_csr_aggregate_select(const Device& dev, const AggregateData<_IdxT> * send_data, const _IdxT * send_len, _IdxT procId, _IdxT * outlen, AggregateData<_IdxT> * out_data);
    static void csr_tentative_prolongation(const Device& dev, _IdxT rows, _IdxT cols, const _IdxT * cluster, _IdxT * tent_row_ptr, _IdxT * tent_col_idx, _ValT * tent_values);
    static void csr_tentative_filter(const Device& dev, _IdxT nrows, _IdxT nblks, COT_SpMVCSRRawMat<_ValT, _IdxT> * Ablks, COT_SpMVCSRRawMat<_IdxT, _IdxT> * strength, COT_SpMVCSRRawMat<_ValT, _IdxT> * A_filter);
    static void csr_tentative_smooth(const Device& dev, _IdxT rowsA, _IdxT colsA, _IdxT colP, const _IdxT * A_row_ptr, const _IdxT * A_col_idx, const _ValT * A_values, const _IdxT * tent_row_ptr, const _IdxT * tent_col_idx, const _ValT * tent_values, const _IdxT * strong_connection, _IdxT * P_row_ptr, _IdxT * P_col_idx, _ValT * P_values, _ValT omega, _IdxT * marker);
    static void rs_connect(const Device& dev, COT_CSRRawMat<_ValT, _IdxT> A, typename TypeInfo<_ValT>::scalar_type eps_strong, COT_CSRRawMat<_IdxT, _IdxT> S, _IdxT * cf);
    static void rs_cfsplit(const Device& dev, COT_CSRRawMat<_ValT, _IdxT> A, COT_CSRRawMat<_IdxT, _IdxT> S, _IdxT * cf, _IdxT * work_lambda, _IdxT * work_ptr, _IdxT * work_cnt, _IdxT * work_i2n, _IdxT * work_n2i);
    static void rs_interpolation(const Device& dev, COT_CSRRawMat<_ValT, _IdxT> A, COT_CSRRawMat<_IdxT, _IdxT> S, const _IdxT * cf, COT_CSRRawMat<_ValT, _IdxT> P, _IdxT * naggr, _IdxT do_trunc, typename TypeInfo<_ValT>::scalar_type eps_trunc, _IdxT coarse_tag, _IdxT fine_tag, _IdxT * work_cidx, _ValT * work_Amin, _ValT * work_Amax);
    static void par_rs_connect(const Device& dev, _IdxT rows, _IdxT nblks, COT_SpMVCSRRawMat<_ValT, _IdxT> * A_blks, typename TypeInfo<_ValT>::scalar_type eps_strong, COT_SpMVCSRRawMat<_IdxT, _IdxT> * S_blks);
    static void par_rs_cfsplit(const Device& dev, COT_CSRRawMat<_ValT, _IdxT> A, COT_CSRRawMat<_IdxT, _IdxT> S, _IdxT * cf, _IdxT * work_lambda, _IdxT * work_ptr, _IdxT * work_cnt, _IdxT * work_i2n, _IdxT * work_n2i);
    static void par_boomeramg_strength(const Device& dev, _IdxT myrank, _IdxT rows, _IdxT nblks, COT_SpMVCSRRawMat<_ValT, _IdxT> * A_blks, const _ValT * diag, typename TypeInfo<_ValT>::scalar_type strong_threshold, typename TypeInfo<_ValT>::scalar_type max_row_sum, _IdxT num_functions, const _IdxT * dof_func, COT_RawCommPattern<_IdxT, _IdxT> * dof_func_exter, COT_SpMVCSRRawMat<_IdxT, _IdxT> * S_blks);
    static void par_boomeramg_coarsen_pmis(const Device& dev, CoarsenPMISStep step, _IdxT myrank, _IdxT rows, _IdxT row_start, _IdxT nblksA, COT_SpMVCSRRawMat<_ValT, _IdxT> * A, _IdxT nblksS, COT_SpMVCSRRawMat<_IdxT, _IdxT> * S, _IdxT * graph_array, COT_RawCommPattern<_IdxT, _IdxT> * graph_array_exter, typename TypeInfo<_ValT>::scalar_type * measure_array, COT_RawCommPattern<typename TypeInfo<_ValT>::scalar_type, _IdxT> * measure_array_exter, _IdxT * CF_marker, COT_RawCommPattern<_IdxT, _IdxT> * CF_marker_exter, _IdxT * graph_size, _IdxT CF_init, _IdxT * graph_array2_work, _IdxT * pSeed);
    static void par_rs_interpolation(const Device& dev, _IdxT myrank, _IdxT rows, _IdxT row_start, _IdxT nblks, COT_SpMVCSRRawMat<_ValT, _IdxT> * A_blks, COT_SpMVCSRRawMat<_IdxT, _IdxT> * S_blks, const _IdxT * cf, COT_RawCommPattern<_IdxT, _IdxT> * cf_exter, COT_CSRRawMat<_ValT, _IdxT> P, _IdxT * naggr, _IdxT do_trunc, typename TypeInfo<_ValT>::scalar_type eps_trunc, _IdxT coarse_tag, _IdxT fine_tag, _IdxT * work_cidx, COT_RawCommPattern<_IdxT, _IdxT> * work_cidx_exter, _ValT * work_Amin, _ValT * work_Amax);
    static void par_boomeramg_interpolation_add_rank_bias(const Device& dev, _IdxT nprocs, _IdxT myrank, _IdxT size, _IdxT * ids, const _IdxT * naggr_per_rank);
    static void par_boomeramg_interpolation_extended_pi(const Device& dev, _IdxT nprocs, _IdxT myrank, _IdxT rows, _IdxT row_start, _IdxT nblks, COT_SpMVCSRRawMat<_ValT, _IdxT> * A_blks, COT_SpMVCSRRawMat<_IdxT, _IdxT> * S_blks, const _IdxT * S_global_to_local, const _ValT * A_diag, _IdxT * cf_loc, COT_RawCommPattern<_IdxT, _IdxT> * cf_exter, COT_CSRRawMat<_ValT, _IdxT> P, _IdxT * naggr, _IdxT * nnzs, _IdxT * strong_f_marker, _IdxT * P_marker_loc, COT_RawCommPattern<_IdxT, _IdxT> * P_marker_exter, _IdxT * fine_to_coarse_loc, COT_RawCommPattern<_IdxT, _IdxT> * file_to_coarse_exter, _IdxT num_functions, _IdxT * dof_func_loc, COT_RawCommPattern<_IdxT, _IdxT> * dof_func_exter);
    static void boomeramg_csr_truncate(const Device& dev, COT_CSRRawMat<_ValT, _IdxT> A, typename TypeInfo<_ValT>::scalar_type trunc_factor, _IdxT max_row_elmts, _IdxT rescale, _IdxT norm_type, _IdxT * ret_row_ptr, _IdxT * ret_row_ptr_end);
}; // end of class SpLevelTransferOps
} // end of namespace hipo
